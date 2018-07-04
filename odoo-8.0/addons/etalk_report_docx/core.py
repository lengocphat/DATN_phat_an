#import xmlrpclib
import base64
from openerp.osv import osv, fields
from openerp import netsvc
from openerp import pooler
from openerp import report
from openerp.osv import orm
from openerp.tools import config
from openerp.tools.translate import _
import logging
import time
import openerp
from datetime import datetime
from docx import *
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import locale
import os

_logger = logging.getLogger(__name__)

SERVICE_NAME_PREFIX = 'report.'
VALID_OUTPUT_TYPES = [('docx', 'Word (docx)')]
DEFAULT_OUTPUT_TYPE = 'docx'

REPORT_TYPE = 'etalk_report'

PATH = os.name == 'nt' and "D:/" or "/tmp/"

locale.setlocale(locale.LC_ALL, '')


def table_replace(document, search, table):
    """
    Replace all occurrences of string with a different string, return updated
    document
    """
    new_doc = document
    search_re = re.compile(search)
    for element in new_doc.iter():
        if element.tag == '{%s}t' % nsprefixes['w']:  # t (text) elements
            if element.text:
                if search_re.search(element.text):
                    parent_map = {c: p for p in document.iter() for c in p}
                    if element in parent_map:
                        parent_map[element].append(table)
                        parent_map[element].remove(element)
    return new_doc


class Etalk_Report(object):
    def __init__(self, name, cr, uid, ids, data, context):
        self.name = name
        self.cr = cr
        self.uid = uid
        self.ids = ids
        self.data = data
        self.context = context or {}
        self.pool = pooler.get_pool(self.cr.dbname)
        self.etalk_content = None  # old : prpt_content
        self.default_output_type = DEFAULT_OUTPUT_TYPE
        self.context_vars = {
            'ids': self.ids,
            'uid': self.uid,
            'context': self.context,
        }

    def setup_report(self):
        ids = self.pool.get('ir.actions.report.xml').search(self.cr, self.uid,
                                                            [('report_name', '=', self.name[len(SERVICE_NAME_PREFIX):]), \
                                                             ('report_type', '=', REPORT_TYPE)], context=self.context)
        if not ids:
            raise orm.except_orm(_('Error'), _("Report service name '%s' is not a etalk report.") % self.name[len(
                SERVICE_NAME_PREFIX):])
        data = self.pool.get('ir.actions.report.xml').read(self.cr, self.uid, ids[0],
                                                           ['etalk_report_output_type', 'etalk_file'])
        self.default_output_type = data['etalk_report_output_type'] or DEFAULT_OUTPUT_TYPE
        self.etalk_content = base64.decodestring(data["etalk_file"])

    def execute(self):
        self.setup_report()
        # returns report and format
        return self.execute_report()

    def execute_report(self):
        output_type = self.data and self.data.get('output_type',
                                                  False) or self.default_output_type or DEFAULT_OUTPUT_TYPE
        if self.etalk_content:
            # NOTE : please fix me when more time

            save_file = open(PATH + 'temp_esop.docx', 'wb')
            save_file.write(self.etalk_content)
            save_file.close()

            templateDocx = zipfile.ZipFile(PATH + 'temp_esop.docx')

            docx = opendocx(PATH + 'temp_esop.docx')
            body = docx.xpath('/w:document/w:body', namespaces=nsprefixes)[0]
            body = self.parse_content_to_document(body)

            # Parse document header to xml:
            list_header = {}
            for file in templateDocx.filelist:
                try:
                    if "word/header" in file.filename:
                        header = self.open_header_docx(templateDocx, file.filename)
                        header_context = header.xpath('/w:hdr', namespaces=nsprefixes)[0]
                        header_context = self.parse_content_to_document(header_context)
                        list_header[file.filename] = header
                except Exception as e:
                    _logger.exception(e)

            newDocx = zipfile.ZipFile(PATH + "content_temp_esop.docx", "w")
            for file in templateDocx.filelist:
                if file.filename != "word/document.xml" and "word/header" not in file.filename:
                    newDocx.writestr(file.filename, templateDocx.read(file))

            with open(PATH + "content_temp_esop.xml", "w+") as tempXmlFile:
                tempXmlFile.write(etree.tostring(docx))
            tempXmlFile.close()
            newDocx.write(PATH + "content_temp_esop.xml", "word/document.xml")

            if list_header:
                for filename, hdr in list_header.iteritems():
                    with open(PATH + "temp_header_esop.xml", "w+") as tempXmlFile:
                        tempXmlFile.write(etree.tostring(hdr))
                    tempXmlFile.close()
                    newDocx.write(PATH + "temp_header_esop.xml", filename)

            templateDocx.close()
            newDocx.close()
            rendered_report = open(PATH + "content_temp_esop.docx", 'rb').read()
        if not rendered_report:
            raise orm.except_orm(_('Error'), _(
                "Etalk report returned no data for the report. Check report definition and parameters."))
        return (rendered_report, output_type)

    def open_header_docx(self, file, filename):
        """Open a docx file, return a header XML tree"""
        xmlcontent = file.read(filename)
        header = etree.fromstring(xmlcontent)
        return header

    def parse_content_to_document(self, body):
        # implement part data at here
        if 'form' in self.data:
            for k, v in self.data['form'].iteritems():
                new_k = "{:" + k + "}"
                new_v = ''
                #field one2many, many2many, many2one
                if isinstance(v, list) and len(v) > 0:
                    try:
                        if isinstance(v[0], (int, long)) and len(v) == 2:  # field many2one
                            new_v = '%s' % (v[1])
                        elif isinstance(v[0], dict):  #field x2many
                            new_v = self.generate_table_x_2_many_fields(v)
                            body = table_replace(body, new_k, new_v)
                            continue
                        elif isinstance(v[0], list):  #field custom
                            new_v = table(v, True, borders={'all': {'color': '345644'}})
                            body = table_replace(body, new_k, new_v)
                            continue
                        else:  #please implement with x2many field
                            new_v = 'not support'
                    except Exception as e:
                        _logger.exception(e)

                elif isinstance(v, (int, float, long)) and not isinstance(v, bool):
                    new_v = v and locale.format('%d', v, 1) or ''

                elif isinstance(v, (str, unicode)) and "-" in v and self.validate_date(v):
                    new_v = self.validate_date(v)
                else:
                    new_v = v if isinstance(v, (str, unicode)) else str(v or '')
                body = replace(body, new_k, new_v)
        return body

    def validate_date(self, date_text):
        try:
            res = ''
            if len(date_text) == 10:
                date = datetime.strptime(str(date_text), '%Y-%m-%d')
                res = date.strftime('%d/%m/%Y')
            if len(date_text) == 19:
                dt = datetime.strptime(str(date_text), '%Y-%m-%d %H:%M:%S')
                res = dt.strftime('%d/%m/%Y %H:%M:%S')

            return res
        except ValueError:
            return False

    def generate_table_x_2_many_fields(self, list_item):
        '''
            generate table from list_tuple
            list_tuple : is list tuple
            body_note : parent note 
        '''
        content_lst = []
        for item in list_item:
            content_item = []
            for k, v in item.iteritems():
                # Remove ID in list
                if k == 'id':
                    continue
                #x2many field
                if isinstance(v, list):
                    if len(v) > 0:
                        if not isinstance(v[0], dict) and len(v) == 2:  # field many2one
                            result = '%s' % (v[1])
                        else:  #please implement with
                            result = 'not support'
                    else:
                        result = ''
                else:
                    result = v if isinstance(v, (str, unicode)) else str(v)
                content_item.append(result)
            content_lst.append(content_item)
        return table(content_lst, True, borders={'all': {'color': '345644'}})


class EtalkReportOpenERPInterface(report.interface.report_int):
    def __init__(self, name):
        super(EtalkReportOpenERPInterface, self).__init__(name)

    def create(self, cr, uid, ids, data, context):
        name = self.name
        report_instance = Etalk_Report(name, cr, uid, ids, data, context)
        rendered_report, output_type = report_instance.execute()
        return rendered_report, output_type


class ir_actions_report_xml(orm.Model):
    _inherit = 'ir.actions.report.xml'

    def __init__(self, pool, cr):
        if self._columns:
            if not ('etalk_report', 'Etalk Report') in self._columns['report_type'].selection:
                self._columns['report_type'].selection.append((REPORT_TYPE, 'Etalk Report'))
        super(ir_actions_report_xml, self).__init__(pool, cr)

    # Code appropriated from webkit example...
    def _lookup_report(self, cr, name):
        """
        Look up a report definition.
        """
        import operator
        import os

        opj = os.path.join

        # First lookup in the deprecated place, because if the report definition
        # has not been updated, it is more likely the correct definition is there.
        # Only reports with custom parser specified in Python are still there.
        if SERVICE_NAME_PREFIX + name in openerp.report.interface.report_int._reports:
            new_report = openerp.report.interface.report_int._reports[SERVICE_NAME_PREFIX + name]
            if not isinstance(new_report, EtalkReportOpenERPInterface):
                new_report = None
        else:
            cr.execute("SELECT * FROM ir_act_report_xml WHERE report_name=%s and report_type=%s", (name, REPORT_TYPE))
            r = cr.dictfetchone()
            if r:
                new_report = EtalkReportOpenERPInterface(SERVICE_NAME_PREFIX + r['report_name'])
            else:
                new_report = None

        if new_report:
            return new_report
        else:
            return super(ir_actions_report_xml, self)._lookup_report(cr, name)

    def etalk_on_change_report_type(self, cr, uid, ids, report_type, model, context=None):
        return {}

    _columns = {
        'etalk_report_output_type': fields.selection([("docx", "DOCX")], 'Output format'),
        'etalk_file': fields.binary('File', filters='*.docx'),
        'etalk_filename': fields.char('Filename', size=256, required=False),
    }