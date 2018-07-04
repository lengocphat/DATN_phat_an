# -*-coding:utf-8-*-
import logging
from openerp.osv import osv, fields
from xlrd import open_workbook
import base64
import thread
from threading import Thread
import datetime
import xlrd
import sys
import codecs
import datetime, xlrd
from xlrd import xldate
from openerp.exceptions import Warning

sys.stdout = codecs.getwriter('utf_8')(sys.stdout)

sys.stdin = codecs.getreader('utf_8')(sys.stdin)


class wk_day_import(osv.osv_memory):
    _name = 'wk.day.import.wizard'
    _description = 'Wizard with step'
    _columns = {
        'file': fields.binary('Data', filters='*.xls'),
        'filename': fields.char('File name'),
        'ts_id': fields.many2one('ts', 'TimeSheet', required=True)
    }

    def convert_cell_to_time_to_float(self,time):
        year, month, day, hour, minute, second = xldate.xldate_as_tuple(time, 0)
        #py_date = datetime.datetime(year, month, day, hour, minute)
        #logging.info(py_date)
        my_time_old = datetime.time(hour // 3600, (minute % 3600) / 60, second % 60)
        my_time = hour + minute/60.0#datetime.time(hour // 3600, (minute % 3600) / 60, second % 60)
        logging.info('-------------old--------------')
        logging.info(my_time_old)
        logging.info('-------------new--------------')
        logging.info(my_time)
        return my_time

    def import_excel_working_day(self, cr, uid, ids, context=None):
        data_file = self.browse(cr, uid, ids)
        if data_file[0].file == False:
            raise osv.except_osv('Validation Error !', 'Dont have file excel to import')
        base_data = base64.decodestring(data_file[0].file)
        xl_workbook  = xlrd.open_workbook(file_contents = base_data)
        colum = 0
        xl_sheet = xl_workbook.sheet_by_index(0)
        excel_title=[u'Ngày', u'Mã Nhân Viên', u'Giờ vào', u'Giờ ra']
        hr_emp_obj= self.pool.get('hr.employee')
        wk_day_obj = self.pool.get('wk.day')
        time = str(data_file[0].ts_id.name).split('-->')
        time_in_limited = datetime.datetime.strptime(time[0], '%d/%m/%Y')
        time_out_limited = datetime.datetime.strptime(time[1], '%d/%m/%Y')
        error_ms = ''
        continue_for_row = False
        for row_idx in range(1, xl_sheet.nrows):  # Iterate through rows
            # default_data
            employee_id = ''
            date = ''
            time_in = 0
            time_out = 0
            try:
                for i_colum in range(0, len(excel_title)):
                    i = xl_sheet.cell(row_idx, i_colum)
                    if excel_title[i_colum] == u'Ngày':
                        logging.info(i.value)
                        flag = datetime.datetime.strptime(str(i.value), '%d/%m/%Y')
                        if flag > time_in_limited and flag < time_out_limited:
                            date = flag
                        else:
                            continue_for_row = True
                            error_ms = error_ms + '\n row' + str(
                                row_idx + 1) + i.value + 'date fail'
                            break
                    elif excel_title[i_colum] == u'Mã Nhân Viên':
                        if i.value:
                            employee_id = hr_emp_obj.search(cr, uid, [('id', '=', int(i.value))])
                            logging.info(employee_id)
                            list_id = wk_day_obj.search(cr, uid, [('employee_id', '=', employee_id), ('date', '=', date)])
                            if list_id:
                                continue_for_row = True
                                error_ms = error_ms + '\n row' + str(
                                    row_idx + 1) + i.value + 'Available'
                                break
                            else:
                                if employee_id == 0:
                                    continue_for_row = True
                                    error_ms = error_ms + '\n row' + str(
                                        row_idx + 1) + i.value + 'not in hr_employee database'
                                    break
                                else:
                                    employee_id = employee_id[0]
                    elif excel_title[i_colum] == u'Giờ vào':
                        if i.value:
                            try:
                                time_in = self.convert_cell_to_time_to_float(i.value)
                            except:
                                raise Warning(
                                    'ô dòng ' + str(int(row_idx) + 1) + ' cột ' + str(int(i_colum)) + 'sai định dạng')
                    elif excel_title[i_colum] == u'Giờ ra':
                        if i.value:
                            try:
                                time_out = self.convert_cell_to_time_to_float(i.value)
                            except:
                                raise Warning(
                                    'ô dòng ' + str(int(row_idx) + 1) + ' cột ' + str(int(i_colum)) + 'sai định dạng')

                if time_out-time_in<0:
                    continue_for_row = False
                    continue
                if continue_for_row:
                    continue_for_row = False
                    continue
                else:
                    total_time = 0
                    total_time_ot = 0
                    if time_out <=14.00:
                        total_time = 12.00 - time_in
                        total_time_ot = 0
                    else:
                        total_time = time_out - time_in - 2.0
                        if total_time > 8.0:
                            total_time_ot = total_time - 8.0
                        else:
                            total_time_ot = 0
                    sql = """
                    INSERT INTO wk_day(date,ts_id,employee_id,time_in,time_out,total_time,total_time_ot) VALUES('%s',%s,%s,%s,%s,%s,%s)
                    """ % (str(date.date()), data_file[0].ts_id.id, employee_id, time_in, time_out , total_time, total_time_ot)
                    logging.info(sql)
                    cr.execute(sql)
                    cr.commit()
            except:
                error_ms = error_ms + '\n row ' + str(
                    row_idx + 1) + " can't import please check Data"
        if error_ms:
            raise Warning(error_ms)
        else:
            raise Warning("Thành công")


        return