# -*-coding:utf-8-*-
import base64
import re
import openerp
import locale
import os
import logging

from openerp.osv import fields
from openerp import pooler
from openerp import report
from openerp.osv import orm
from openerp.tools.translate import _
import zipfile
from datetime import datetime
from docx import *
try:
    from mailmerge import MailMerge
except:
    from mailmerge import main
from copy import deepcopy


_logger = logging.getLogger(__name__)

SERVICE_NAME_PREFIX = 'report.'
VALID_OUTPUT_TYPES = [('docx', 'Word (docx)')]
DEFAULT_OUTPUT_TYPE = 'docx'

REPORT_TYPE = 'hrs_report'

PATH = os.name == 'nt' and "D:/" or os.path.expanduser('~') + '/'

locale.setlocale(locale.LC_ALL, '')

RELS_ZIP_PATH          = "word/_rels/document.xml.rels"
DOC_ZIP_PATH           = "word/document.xml"
CONTENT_TYPES_PATH     = "[Content_Types].xml"
ALT_CHUNK_TYPE         = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/aFChunk"
ALT_CHUNK_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"

GENSHI_EXPR = re.compile(r'''
        (/)?                                 # is this a closing tag?
        (for|if)  # tag directive
        \s*
        (?:\s(\w+)\s (in|==|<>) \s(.*)|$)         # match a single attr & its value
        |
        .*                                   # or anything else
        ''', re.VERBOSE)

def table_replace(document, search, table):
    """
    Replace all occurences of string with a different string, return updated
    document
    """
    newdocument = document
    searchre = re.compile(search)
    for element in newdocument.iter():
        if element.tag == '{%s}t' % nsprefixes['w']:  # t (text) elements
            if element.text:
                if searchre.search(element.text):
                    parent_map = {c: p for p in document.iter() for c in p}
                    if element in parent_map:
                        parent_map[element].append(table)
                        parent_map[element].remove(element)
    return newdocument

def wrap_nodes_between(first, last, new_nodes):
    """An helper function to move all nodes between two nodes to a new node
    and add that new node to their former parent. The boundary nodes are
    removed in the process.
    """
    old_parent = first.getparent()

#     for node in first.itersiblings():
#         if node is last:
#             break
#         # appending a node to a new parent also
#         # remove it from its previous parent
#         new_nodes.append(node)
    
    curr_index = old_parent.index(first)
    
    #Remove all nodes between first and last
    for index in range(old_parent.index(first) +1, old_parent.index(last)):
        old_parent.remove(old_parent[index])
    
    for index,node in enumerate(new_nodes):
        if index == 0:
            old_parent.replace(first, node)
        else:
            old_parent.insert(curr_index + index, node)
#     new_parent.tail = last.tail
    
    if not new_nodes:
        old_parent.remove(first)
    old_parent.remove(last)

class Hrs_Report(object):
    def __init__(self, name, cr, uid, ids, data, context):
        self.name = name
        self.cr = cr
        self.uid = uid
        self.ids = ids
        self.data = data
        self.context = context or {}
        self.pool = pooler.get_pool(self.cr.dbname)
        self.hrs_content = None  # old : prpt_content
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
            raise orm.except_orm(_('Error'), _("Report service name '%s' is not a hrs report.") % self.name[len(
                SERVICE_NAME_PREFIX):])
        data = self.pool.get('ir.actions.report.xml').read(self.cr, self.uid, ids[0],
                                                           ['hrs_report_output_type', 'hrs_file'])
        self.default_output_type = data['hrs_report_output_type'] or DEFAULT_OUTPUT_TYPE
        self.hrs_content = base64.decodestring(data["hrs_file"])

    def execute(self):
        self.setup_report()
        # returns report and format
        return self.execute_report()

    def execute_report(self):
        output_type = self.data and self.data.get('output_type',
                                                  False) or self.default_output_type or DEFAULT_OUTPUT_TYPE
        multi = self.data and self.data.get('multi', False) or False
        merge_multi_report_in_single_doc = self.data and self.data.get('merge_multi_report', False) or False
        parse_condition = self.data and self.data.get('parse_condition', False) or False
        list_data = self.data and self.data.get('form', False) or False
        rendered_report = False
        
        if self.hrs_content and multi and list_data:
            rendered_report = self.merge_multi_report(list_data)
        
        elif self.hrs_content and merge_multi_report_in_single_doc and list_data:
            option = {'parse_condition': parse_condition}
            rendered_report = self.merge_multi_report_in_single_doc(list_data, option)
            
        elif self.hrs_content and not multi:
            # NOTE : please fix me when more time

            save_file = open(PATH + 'temp.docx', 'wb')
            save_file.write(self.hrs_content)
            save_file.close()

            templateDocx = zipfile.ZipFile(PATH + 'temp.docx')

            docx = opendocx(PATH + 'temp.docx')
            body = docx.xpath('/w:document/w:body', namespaces=nsprefixes)[0]
            
            #Temporary only parse if have 
            if parse_condition:
                self.parse_content_with_condition(body)
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

            #Parse document footer to xml
            list_footer = {}
            for file in templateDocx.filelist:
                try:
                    if "word/footer" in file.filename:
                        footer = self.open_header_docx(templateDocx, file.filename)
                        footer_context = footer.xpath('/w:ftr', namespaces=nsprefixes)[0]
                        footer_context = self.parse_content_to_document(footer_context)
                        list_footer[file.filename] = footer
                except Exception as e:
                    _logger.exception(e)

            newDocx = zipfile.ZipFile(PATH + "content_temp.docx", "w")
            for file in templateDocx.filelist:
                if file.filename != "word/document.xml" and "word/header" not in file.filename and "word/footer" not in file.filename:
                    newDocx.writestr(file.filename, templateDocx.read(file))

            with open(PATH + "content_temp.xml", "w+") as tempXmlFile:
                tempXmlFile.write(etree.tostring(docx))
            tempXmlFile.close()
            newDocx.write(PATH + "content_temp.xml", "word/document.xml")
            if os.path.isfile(PATH + "content_temp.xml"):
                os.remove(PATH + "content_temp.xml")

            if list_header:
                for filename, hdr in list_header.iteritems():
                    with open(PATH + "temp_header.xml", "w+") as tempXmlFile:
                        tempXmlFile.write(etree.tostring(hdr))
                    tempXmlFile.close()
                    newDocx.write(PATH + "temp_header.xml", filename)
                    if os.path.isfile(PATH + "temp_header.xml"):
                        os.remove(PATH + "temp_header.xml")
            
            #Addtion to parse data in footer
            if list_footer:
                for filename, ftr in list_footer.iteritems():
                    with open(PATH + "temp_footer.xml", "w+") as tempXmlFile:
                        tempXmlFile.write(etree.tostring(ftr))
                    tempXmlFile.close()
                    newDocx.write(PATH + "temp_footer.xml", filename)
                    if os.path.isfile(PATH + "temp_footer.xml"):
                        os.remove(PATH + "temp_footer.xml")

            templateDocx.close()
            newDocx.close()
            rendered_report = open(PATH + "content_temp.docx", 'rb').read()
            
            if self.context.get('is_delete_temp_file', True):
                if os.path.isfile(PATH + "content_temp.docx"):
                    os.remove(PATH + "content_temp.docx")
                    
            if os.path.isfile(PATH + "temp.docx"):
                os.remove(PATH + "temp.docx")

        if not rendered_report:
            raise orm.except_orm(_('Error'), _(
                "hrs report returned no data for the report. Check report definition and parameters."))
        return rendered_report, output_type

    def merge_multi_report(self, list_data):
        input_file = open(PATH + 'temp.docx', 'wb')
        input_file.write(self.hrs_content)
        input_file.close()
        #document = MailMerge(PATH + 'temp.docx')
        document.merge_pages(list_data)
        document.write(PATH + 'output.docx')
        rendered_report = open(PATH + "output.docx", 'rb').read()
        if os.path.isfile(PATH + "output.docx"):
            os.remove(PATH + "output.docx")
        return rendered_report

    def open_header_docx(self, file, filename):
        """Open a docx file, return a header XML tree"""
        xmlcontent = file.read(filename)
        header = etree.fromstring(xmlcontent)
        return header
    
    def search_tag_in_document(self, tree):
        """
        Tag like <for>  </for>
        """
        def check_except_directive( expr):
            if GENSHI_EXPR.match(expr).groups()[1] is not None:
                return False
            return True
        text_input = '{%s}t' % nsprefixes['w']
        s_xpath = "//w:t[contains(.,'<') and contains(.,'>')]"
        
        r_statements = []
        opened_tags = []
        # We map each opening tag with its closing tag
        closing_tags = {}                   
        for statement in tree.xpath(s_xpath, namespaces=nsprefixes):
            if statement.tag == text_input:
                expr = statement.text[1:-1]
                expr = check_except_directive(expr) and statement.text[1:-1] or expr
          
            if not expr:
                raise OOTemplateError("No expression in the text", self.filepath)
            closing, directive, attr, operator, attr_val = GENSHI_EXPR.match(expr).groups()
            _logger.info('(vhr_report_docx) Parse condition from "%s" to %s,%s,%s,%s'% (expr,directive,attr,operator,attr_val))
            is_opening = closing != '/'
            
            if directive is not None:
                # map closing tags with their opening tag
                if is_opening:
                    opened_tags.append(statement)
                else:
                    closing_tags[id(opened_tags.pop())] = statement
                # - we only need to return opening statements
                if is_opening:
                    r_statements.append((statement,
                                         (expr, directive, attr, operator, attr_val))
                                       )
        assert not opened_tags
        return r_statements, closing_tags

    
    def parse_content_with_condition(self, tree):
        table_namespace = nsprefixes['w']
        table_row_tag = '{%s}tbl' % table_namespace
        
        r_statements, closing_tags = self.search_tag_in_document(tree)

        for r_node, parsed in r_statements:
            expr, directive, attr, operator, a_val = parsed
            
            # If the node is a directive statement:
            if directive is not None:
                opening = r_node
                closing = closing_tags[id(r_node)]

                # - we find the nearest common ancestor of the closing and
                #   opening statements
                o_ancestors = [opening]
                c_ancestors = [closing] + list(closing.iterancestors())
                ancestor = None
                for node in opening.iterancestors():
                    try:
                        idx = c_ancestors.index(node)
                        assert c_ancestors[idx] == node
                        # we only need ancestors up to the common one
                        del c_ancestors[idx:]
                        ancestor = node
                        break
                    except ValueError:
                        # c_ancestors.index(node) raise ValueError if node is
                        # not a child of c_ancestors
                        pass
                    o_ancestors.append(node)
                assert ancestor is not None, \
                       "No common ancestor found for opening and closing tag"

                outermost_o_ancestor = o_ancestors[-1]
                outermost_c_ancestor = c_ancestors[-1]

                # handle horizontal repetitions (over columns)
                if directive == "for" and ancestor.tag == table_row_tag and operator == 'in':
                    self._handle_column_loops(parsed, ancestor,
                                                      opening,
                                                      outermost_o_ancestor,
                                                      outermost_c_ancestor)
                elif directive == 'if':
                    self._handle_condition(parsed, ancestor,
                                                      opening,
                                                      outermost_o_ancestor,
                                                      outermost_c_ancestor)
                    
    
    def _handle_condition(self, statement, ancestor, opening, outer_o_node, outer_c_node):
        position_xpath_expr = 'count(preceding-sibling::*)'
        opening_pos =  int(outer_o_node.xpath(position_xpath_expr, namespaces=nsprefixes))
        closing_pos =  int(outer_c_node.xpath(position_xpath_expr, namespaces=nsprefixes))
        first = ancestor[opening_pos]
        last = ancestor[closing_pos]
        
        _, directive, attr, operator, a_val = statement
        value = self.data['form'].get(attr, False)
        if operator == '<>':
            operator = '!='
        
        #dont compare with empty string,
        if not value and isinstance(value,(str,unicode)):
            value = 'False'
        elif value and isinstance(value,(str,unicode)):
            value = "'" + value + "'" 
        
        res = eval(str(value) + operator+a_val)
        #If comparison is correct, remove condition
        if res:
            ancestor.remove(first)
            ancestor.remove(last)
        else:
            _logger.info('Remove all data within condition: %s %s %s %s'%(directive,attr,operator,a_val))
            #comparison return false ==> need to remove everything between first and last
            list = range(opening_pos +1, closing_pos)
            list.reverse()
            for index in list:
                node = ancestor[index]
                ancestor.remove(node)
            
            ancestor.remove(first)
            ancestor.remove(last)
        
        
        
        
    def _handle_column_loops(self, statement, ancestor, opening, outer_o_node, outer_c_node):
        _, directive, attr, operator, a_val = statement

        self.has_col_loop = True

        table_namespace = nsprefixes['w']
        table_row_tag = '{%s}tr' % table_namespace
        table_col_tag = '{%s}tc' % table_namespace
        
        table_node = ancestor
        # add counting instructions
        loop_id = id(opening)

        enclosed_cell = outer_o_node.getnext()
        assert enclosed_cell.tag == table_row_tag

        position_xpath_expr = 'count(preceding-sibling::*)'
        opening_pos =  int(outer_o_node.xpath(position_xpath_expr, namespaces=nsprefixes))
        closing_pos =  int(outer_c_node.xpath(position_xpath_expr, namespaces=nsprefixes))

        # compute the column header nodes corresponding to
        # the opening and closing tags.
        first = table_node[opening_pos]
        last = table_node[closing_pos]
        
        wrap_node = []
        if self.data.get('form', False):
            xpath="//w:t[contains(.,'{:') and contains(.,'}')]"
            for data in self.data['form'].get(a_val, []):
                for index in range(opening_pos +1, closing_pos):
                    copy_node = deepcopy(table_node[index])
                    for node in copy_node.xpath(xpath,namespaces=nsprefixes):
                        old_data = node.text
                        value = old_data[2:-1]
                        value = value.replace(attr, 'data', 1)
                        value = value.replace('[', "['")
                        value = value.replace(']', "']")
                        
                        new_data = eval(value)
                        if isinstance(new_data, (int,float)):
                            new_data = new_data and locale.format('%d', new_data, 1) or ''
                            
                        node = self.replace(node, old_data, new_data)
                        
                    wrap_node.append(copy_node)
                    
        wrap_nodes_between(first, last, wrap_node)
    
    def replace(self, document, search, replace):
        """
        Replace all occurences of string with a different string, return updated
        document
        """
        newdocument = document
        searchre = re.compile(re.escape(search))
        for element in newdocument.iter():
            if element.tag == '{%s}t' % nsprefixes['w']:  # t (text) elements
                if element.text:
                    if searchre.search(element.text):
                        element.text = re.sub(re.escape(search), replace, element.text)
        return newdocument
    
    def parse_content_to_document(self, body):
        # implement part data at here
        if 'form' in self.data:
            for k, v in self.data['form'].iteritems():
                new_k = "{:" + k + "}"
                new_v = ''

                is_replace_already = False
                #field one2many, many2many, many2one
                if isinstance(v, list) and len(v) > 0:
                    try:
                        if isinstance(v[0], (int, long)) and len(v) == 2:  # field many2one
                            new_v = '%s' % (v[1])
                        elif isinstance(v[0], (str, unicode)) and len(v) == 1:
                            v = etree.XML(v[0].encode('utf-8'))
                            v = v.getchildren()
                            advReplace(body, new_k, v)
                            continue
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
                    #Case have line break
                    if isinstance(v, (str, unicode)) and "\\n" in v:
                        list_data = v.split("\\n")

                        #Get element of field text in file xml
                        searchre = re.compile(new_k)

                        for element in body.iter():
                            if element.tag == '{%s}t' % nsprefixes['w']:  # t (text) elements
                                if element.text:
                                    if searchre.search(element.text):
                                        is_replace_already = True
                                        parent_element = element.getparent()
                                        for data in list_data:
                                            if list_data.index(data) != 0:
                                                parent_element.append(makeelement('br'))
                                            parent_element.append(makeelement('t', tagtext=data))

                                        element.text = re.sub(new_k, '', element.text)
                                        break

                        if not is_replace_already:
                            new_v = v if isinstance(v, (str, unicode)) else str(v or '')

                    else:
                        new_v = v if isinstance(v, (str, unicode)) else str(v or '')

                if not is_replace_already:
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

    
    def make_section_break_next_page(self, orient='portrait'):
        """ Insert a break, default 'page'.
        See http://openxmldeveloper.org/forums/thread/4075.aspx
        Return our page break element."""
        # Need to enumerate different types of page breaks.
        pagebreak = makeelement('p')
        
        pPr = makeelement('pPr')
        sectPr = makeelement('sectPr')
        footnotePr = makeelement('footnotePr')
        numRestart = makeelement('numRestart', attributes={'val':'eachSect'})
        footnotePr.append(numRestart)
        
        if orient == 'portrait':
            pgSz = makeelement('pgSz', attributes={'w': '12240', 'h': '15840'})
        elif orient == 'landscape':
            pgSz = makeelement('pgSz', attributes={'h': '12240', 'w': '15840',
                                                   'orient': 'landscape'})
            
        sectPr.append(footnotePr)
        sectPr.append(pgSz)
        pPr.append(sectPr)
        pagebreak.append(pPr)
        return pagebreak

    def merge_multi_report_in_single_doc(self, list_data, option):
        self.context['is_delete_temp_file'] = False
        ouput_file = 'result.docx'
        
        for i, data in enumerate(list_data):
            if os.path.isfile(PATH + "content_temp.docx"):
                os.remove(PATH + "content_temp.docx")
                     
            self.name = data.keys()[0]
            data = data.values()[0]
             
            rendered_report = False
            #Generate self.hrs_content
            self.setup_report()
            self.data = {'form': data}
            self.data.update(option)
            rendered_report, output_type = self.execute_report()
            
            if i < len(list_data)-1:
                self.add_section_into_file("content_temp.docx")
                
            if i == 0:
                #Copy file content_temp.docx to output file
                os.rename(PATH + "content_temp.docx", PATH + ouput_file)
            else:
                
                output_docx = zipfile.ZipFile(PATH + ouput_file)
                self.merge_file(output_docx, "content_temp.docx", i+1)
        
        rendered_report = open(PATH + ouput_file, 'rb').read()
        
        if os.path.isfile(PATH + "result.docx"):
            os.remove(PATH + "result.docx")
        if os.path.isfile(PATH + "content_temp.docx"):
            os.remove(PATH + "content_temp.docx")
            
        return rendered_report
    
    
    def add_section_into_file(self, filename):
        
        #Add section
        docx = opendocx(PATH + filename)
        body = docx.xpath('/w:document/w:body', namespaces=nsprefixes)[0]
        body.append(self.make_section_break_next_page())
        
        content_temp = zipfile.ZipFile(PATH + filename)
        newDocx = zipfile.ZipFile(PATH + "content_temp_section_break.docx", "w")
        for file in content_temp.filelist:
            if file.filename not in [DOC_ZIP_PATH]:
                newDocx.writestr(file.filename, content_temp.read(file))
         
        with open(PATH + 'temp_xml.xml', "w+") as tempXmlFile:
            tempXmlFile.write(etree.tostring(docx))
        tempXmlFile.close()
        newDocx.write(PATH + "temp_xml.xml", "word/document.xml")
         
        if os.path.isfile(PATH + filename):
            os.remove(PATH + filename)
        
        if os.path.isfile(PATH + 'temp_xml.xml'):
            os.remove(PATH + 'temp_xml.xml')
             
        os.rename(PATH + "content_temp_section_break.docx", PATH + filename)
        
    
    def merge_file(self, output_docx, add_docx_file, index):
#         content = open(PATH + add_docx_file, 'rb').read()
        
        zipname = 'part'+ str(index) +'.docx'
        refID = 'rId10'+ str(index)
        
        newDocx = zipfile.ZipFile(PATH + "result_temp.docx", "w")
        for file in output_docx.filelist:
            if file.filename not in [RELS_ZIP_PATH, DOC_ZIP_PATH, CONTENT_TYPES_PATH]:
                newDocx.writestr(file.filename, output_docx.read(file))
                
        #add new docx file
        newDocx.write(PATH + add_docx_file,  zipname)
        
        #Add reference
        self.addReference(output_docx, newDocx, zipname, refID)
#         
#         #Add AltChunk
        self.addAltChunk(output_docx, newDocx, refID)
#         
#         #Add Content Type
        self.addContentType(output_docx, newDocx, zipname)
        
        if os.path.isfile(PATH + "result.docx"):
            os.remove(PATH + "result.docx")
            
        os.rename(PATH + "result_temp.docx", PATH + "result.docx")
        
    
        
    def addReference(self, output_docx, newDocx, zipName, refID):
        relXmlString = '<Relationship Target="../' +zipName +'" Type="' +ALT_CHUNK_TYPE +'" Id="'+refID +'"/>'
        with open(PATH + "temp_rels.xml", "w+") as tempFile:
            content = output_docx.read(RELS_ZIP_PATH)
            pos = content.index('</Relationships>')
            tempFile.write(content)
            tempFile.seek(pos)
            tempFile.write(relXmlString)
            tempFile.write('</Relationships>')
        tempFile.close()
        newDocx.write(PATH + "temp_rels.xml", RELS_ZIP_PATH)
        
        if os.path.isfile(PATH + 'temp_rels.xml'):
            os.remove(PATH + 'temp_rels.xml')
    
    def addAltChunk(self, output_docx, newDocx, refID):
        xmlItem = '<w:altChunk r:id="'+ refID +'"/>'
        
        with open(PATH + "temp_chunk.xml", "w+") as tempFile:
            content = output_docx.read(DOC_ZIP_PATH)
            pos = content.index('</w:body>')
            tempFile.write(content)
            tempFile.seek(pos)
            tempFile.write(xmlItem)
            tempFile.write('</w:body></w:document>')
        tempFile.close()
        newDocx.write(PATH + "temp_chunk.xml", DOC_ZIP_PATH)
        
        if os.path.isfile(PATH + 'temp_chunk.xml'):
            os.remove(PATH + 'temp_chunk.xml')
    
    def addContentType(self, output_docx, newDocx, zipName):
        xmlItem = '<Override ContentType="' + ALT_CHUNK_CONTENT_TYPE + '" PartName="/' + zipName +'"/>'
        
        with open(PATH + "temp_content_type.xml", "w+") as tempFile:
            content = output_docx.read(CONTENT_TYPES_PATH)
            pos = content.index('</Types>')
            tempFile.write(content)
            tempFile.seek(pos)
            tempFile.write(xmlItem)
            tempFile.write('</Types>')
        tempFile.close()
        newDocx.write(PATH + "temp_content_type.xml", CONTENT_TYPES_PATH)
        
        if os.path.isfile(PATH + 'temp_content_type.xml'):
            os.remove(PATH + 'temp_content_type.xml')
        
    
class hrsReportOpenERPInterface(report.interface.report_int):
    def __init__(self, name):
        super(hrsReportOpenERPInterface, self).__init__(name)

    def create(self, cr, uid, ids, data, context):
        name = self.name
        report_instance = Hrs_Report(name, cr, uid, ids, data, context)
        rendered_report, output_type = report_instance.execute()
        return rendered_report, output_type


class ir_actions_report_xml(orm.Model):
    _inherit = 'ir.actions.report.xml'

    def __init__(self, pool, cr):
        if self._columns:
            if not ('hrs_report', 'hrs Report') in self._columns['report_type'].selection:
                self._columns['report_type'].selection.append((REPORT_TYPE, 'hrs Report'))
            if not ('xlsx', 'Xlsx Report') in self._columns['report_type'].selection:
                self._columns['report_type'].selection.append(('xlsx', 'Xlsx Report'))

            if not ('aeroo', 'Aeroo Report') in self._columns['report_type'].selection:
                self._columns['report_type'].selection.append(('aeroo', 'Aeroo Report'))
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
            if not isinstance(new_report, hrsReportOpenERPInterface):
                new_report = None
        else:
            cr.execute("SELECT * FROM ir_act_report_xml WHERE report_name=%s and report_type=%s", (name, REPORT_TYPE))
            r = cr.dictfetchone()
            if r:
                new_report = hrsReportOpenERPInterface(SERVICE_NAME_PREFIX + r['report_name'])
            else:
                new_report = None

        if new_report:
            return new_report
        else:
            return super(ir_actions_report_xml, self)._lookup_report(cr, name)

    def hrs_on_change_report_type(self, cr, uid, ids, report_type, model, context=None):
        return {}

    _columns = {
        'hrs_report_output_type': fields.selection([("docx", "DOCX")], 'Output format'),
        'hrs_file': fields.binary('File', filters='*.docx'),
        'hrs_filename': fields.char('Filename', size=256, required=False),  #
    }

