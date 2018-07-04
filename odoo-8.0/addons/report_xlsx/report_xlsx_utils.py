# -*- coding: utf-8 -*-
from openerp.osv import orm
from report_xlsx import report_xlsx


class generic_report_xlsx_base(report_xlsx):
    def __init__(self, name, table, rml=False, parser=False, header=True, store=False):
        super(generic_report_xlsx_base, self).__init__(name, table, rml, parser, header, store)

    def get_cell_style(self, wb, styles, cell_style_format=None):
        """
        Get default style for the cell
        @param styles: list of style which want to use
        @rtype: rowstyle 
        """
        res_style = {}
        for style in styles:
            res_style[style] = self.xls_styles[style]
        if cell_style_format:
            res_style['num_format'] = cell_style_format
        return wb.add_format(res_style)

    def generate_style(self, workbook):
        # Set Default Cell Styles
        self.date_format = 'DD-MM-YYYY'
        self.decimal_format = '#,##0'

        self.style_date = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'num_format': 'dd/mm/yyyy', 'text_wrap': True})
        self.style_date_right = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'num_format': 'dd/mm/yyyy', 'align': 'right', 'text_wrap': True})
        self.style_date_right_border = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'num_format': 'dd/mm/yyyy', 'align': 'right', 'text_wrap': True,
             'border': 1})
        self.style_date_center_border = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'num_format': 'dd/mm/yyyy', 'align': 'center', 'text_wrap': True,
             'border': 1})

        self.style_decimal = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'num_format': '#,##0', 'text_wrap': True})
        self.style_decimal_border = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'num_format': '#,##0', 'text_wrap': True, 'border': 1})
        self.style_decimal_bold = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'num_format': '#,##0', 'bold': True, 'text_wrap': True})
        self.style_decimal_bold_border = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'num_format': '#,##0', 'bold': True, 'text_wrap': True,
             'border': 1})
        self.style_default_decimal_border = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'num_format': '#,##0.00', 'text_wrap': True, 'border': 1})

        self.normal_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'align': 'center', 'valign': 'vjustify', 'text_wrap': True})
        self.normal_style_right = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'align': 'right', 'valign': 'vjustify', 'text_wrap': True})
        self.normal_style_left = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'align': 'left', 'valign': 'vjustify', 'text_wrap': True})
        self.normal_style_center = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        self.normal_style_center_nowrap = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'text_wrap': False})
        self.normal_style_left_borderall = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'align': 'left', 'valign': 'vjustify', 'border': 1,
             'text_wrap': True})
        self.normal_style_right_borderall = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'align': 'right', 'valign': 'vjustify', 'border': 1,
             'text_wrap': True})
        self.normal_style_italic = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'align': 'center', 'valign': 'vjustify', 'italic': True,
             'text_wrap': True})

        self.normal_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'align': 'left', 'text_wrap': True})
        self.normal_style_borderall = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'text_wrap': True})
        self.normal_style_center_bold = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'bold': True,
             'text_wrap': True})
        self.normal_style_bold_left_borderall = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'align': 'left', 'valign': 'vjustify', 'bold': True,
             'text_wrap': True, 'border': 1})
        self.normal_style_bold_borderall = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'bold': True, 'border': 1,
             'text_wrap': True})
        self.normal_style_left_bold = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'align': 'left', 'valign': 'vcenter', 'bold': True,
             'text_wrap': True})

        self.blank_big_style_borderall = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 50, 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'text_wrap': True})

        self.cell_title_style = workbook.add_format(
            {'font_name': 'Arial', 'align': 'center', 'valign': 'vcenter', 'bold': True, 'text_wrap': True,
             'font_size': 18})
        self.cell_title_center_style = workbook.add_format(
            {'font_name': 'Arial', 'align': 'center', 'valign': 'vcenter', 'bold': True, 'text_wrap': True,
             'font_size': 20})
        self.cell_title_left_style = workbook.add_format(
            {'font_name': 'Arial', 'align': 'left', 'valign': 'vcenter', 'bold': True, 'text_wrap': True,
             'font_size': 20})
        self.normal_style_left_nowrap = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'align': 'left', 'valign': 'vjustify', 'text_wrap': False})

        # normal cell

    def generate_xls_report(self, _p, _xs, data, objects, wb, report_name='Report Name'):
        """
        This function will generate excel report.
        We setup some configurations for the sheet by defaults
        @return: worksheet object 
        """

        self.generate_style(wb)
        # set print sheet
        # cell_overwirte_ok => allow to merge cell in the sheet
        ws, _row_pos = self.generate_worksheet(_p, _xs, data, objects, wb, report_name, count=0)

        # # set print header/footer
        #         ws.header_str = self.xls_headers['standard']
        #         ws.footer_str = self.xls_footers['standard']

        return ws

    def generate_worksheet(self, _p, _xs, data, objects, wb, report_name, count=0):
        """
        @summary: get new worksheet from workbook, reset current row position in the new worksheet 
        @return: new worksheet, new row_pos
        """
        report_name = count and (report_name[:31] + ' ' + str(count)) or report_name[:31]
        ws = wb.add_worksheet(report_name)
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_num_pages = 1
        ws.fit_height_to_pages = 0
        ws.fit_width_to_pages = 1  # allow to print fit one page
        row_pos = 0

        return ws, row_pos


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

class ir_actions_report_xml(orm.Model):
    _inherit = 'ir.actions.report.xml'

    def __init__(self, pool, cr):
        if not ('xlsx', 'XLSX') in self._columns['report_type'].selection:
            self._columns['report_type'].selection.append(('xlsx', 'XLSX'))
        super(ir_actions_report_xml, self).__init__(pool, cr)