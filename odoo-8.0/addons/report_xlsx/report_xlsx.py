# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Trobz (trobz.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import xlsxwriter
from xlwt.Style import default_style
import inspect
from types import CodeType
from openerp import pooler
import time
import logging
from openerp.report.report_sxw import * # @UnusedWildImport
_logger = logging.getLogger(__name__)


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class report_xlsx(report_sxw):

    xls_types = {
        'bool': xlsxwriter.worksheet.Worksheet.write,
        'date': xlsxwriter.worksheet.Worksheet.write,
        'text': xlsxwriter.worksheet.Worksheet.write,
        'number': xlsxwriter.worksheet.Worksheet.write,
        'blank': xlsxwriter.worksheet.Worksheet.write
        }
    
    xls_types_default = {
        'bool': False,
        'date': None,
        'text': '',
        'blank': '',
        'number': 0,
    }
    
    xls_styles = {
    }
    # TO DO: move parameters supra to configurable data

    def create(self, cr, uid, ids, data, context=None):
        self.pool = pooler.get_pool(cr.dbname)
        self.cr = cr
        self.uid = uid
        report_obj = self.pool.get('ir.actions.report.xml')
        report_ids = report_obj.search(cr, uid,
                [('report_name', '=', self.name[7:])], context=context)
        if report_ids:
            report_xml = report_obj.browse(cr, uid, report_ids[0], context=context)
            self.title = report_xml.name
            if report_xml.report_type == 'xlsx':
                return self.create_source_xls(cr, uid, ids, data, context)
        elif context.get('xlsx_export'):
            self.table = data.get('model') or self.table   # use model from 'data' when no ir.actions.report.xml entry
            return self.create_source_xls(cr, uid, ids, data, context)
        return super(report_xlsx, self).create(cr, uid, ids, data, context)

    def create_source_xls(self, cr, uid, ids, data, context=None):
        if not context:
            context = {}
        parser_instance = self.parser(cr, uid, self.name2, context)
        self.parser_instance = parser_instance
        objs = self.getObjects(cr, uid, ids, context)
        parser_instance.set_context(objs, data, ids, 'xlsx')
        objs = parser_instance.localcontext['objects']
        n = cStringIO.StringIO()
        
        start_time = time.time()
        
        wb = xlsxwriter.Workbook(n, {'constant_memory': False})
        _p = AttrDict(parser_instance.localcontext)
        _xs = self.xls_styles

        self.generate_xls_report(_p, _xs, data, objs, wb)
        n.seek(0)
        wb.close()
        _logger.info("End process %s (%s), elapsed time: %s" % (self.name, self.table, time.time() - start_time)) # debug mode
        return (n.read(), 'xlsx')

    def render(self, wanted, col_specs, rowtype, render_space='empty'):
        """
        returns 'evaluated' col_specs

        Input:
        - wanted: element from the wanted_list
        - col_specs : cf. specs[1:] documented in xls_row_template method
        - rowtype : 'header' or 'data'
        - render_space : type dict, (caller_space + localcontext) if not specified
        """
        if render_space == 'empty':
            render_space = {}
            caller_space = inspect.currentframe().f_back.f_back.f_locals
            localcontext = self.parser_instance.localcontext
            render_space.update(caller_space)
            render_space.update(localcontext)
        row = col_specs[wanted][rowtype][:]
        for i in range(len(row)):
            if isinstance(row[i], CodeType):
                # we log if there are any errors
                try:
                    row[i] = eval(row[i], render_space)
                except:
                    _logger.warn('Eval error %s .',row[i])    
        row.insert(0, wanted)
        return row

    def generate_xls_report(self, parser, xls_styles, data, objects, wb):
        """ override this method to create your excel file """
        raise NotImplementedError()

    def xls_row_template(self, specs, wanted_list):
        """
        Returns a row template.

        Input :
        - 'wanted_list': list of Columns that will be returned in the row_template
        - 'specs': list with Column Characteristics
            0: Column Name (from wanted_list)
            1: Column Colspan
            2: Column Size (unit = the width of the character ’0′ as it appears in the sheet’s default font)
            3: Column Type
            4: Column Data
            5: Column Formula (or 'None' for Data)
            6: Column Style
        """
        r = []
        col = 0
        for w in wanted_list:
            found = False
            for s in specs:
                if s[0] == w:
                    found = True
                    s_len = len(s)
                    c = list(s[:5])
                    # set write_cell_func or formula
                    if s_len > 5 and s[5] is not None:
                        c.append({'formula': s[5]})
                    else:
                        c.append({'write_cell_func': report_xlsx.xls_types[c[3]]})
                    # Set custom cell style
                    if s_len > 6 and s[6] is not None:
                        c.append(s[6])
                    else:
                        c.append(None)
                    # Set cell formula
                    if s_len > 7 and s[7] is not None:
                        c.append(s[7])
                    else:
                        c.append(None)
                    r.append((col, c[1], c))
                    col += c[1]
                    break
            if not found:
                _logger.warn("report_xls.xls_row_template, column '%s' not found in specs", w)
        return r

    def xls_write_row(self, ws, row_pos, row_data, row_style=default_style, set_column_size=False):
        for col, size, spec in row_data:
            data = spec[4]
            formula = spec[5].get('formula') or None
            style = spec[6] and spec[6] or row_style
            if not data:
                # if no data, use default values
                data = report_xlsx.xls_types_default[spec[3]]
            if size != 1:
                if formula:
                    ws.merge_range(row_pos, col, row_pos, col + size - 1, data, style)
                else:
                    ws.merge_range(row_pos, col, row_pos, col + size - 1, data, style)
            else:
                if formula:
                    ws.write_formula(row_pos, col, formula, style)
                else:
                    try:
                        spec[5]['write_cell_func'](ws, row_pos, col, data, style)
                    except:
                        _logger.warn('Error at spec: %s .',spec)
            if set_column_size:
                ws.set_column(col, col, spec[2])
        return row_pos + 1

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
