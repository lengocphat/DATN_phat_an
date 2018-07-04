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
from openerp.exceptions import Warning
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
from datetime import datetime

class ts(osv.osv):
    _name = 'ts'

    def onchange_date(self,cr, uid, ids, date_start, date_end, context=None):
        res = {'value': {'name': '', 'month': 0, 'year': 0}, 'warning': {}}

        if date_start and date_end:
            date_start = datetime.strptime(date_start, DEFAULT_SERVER_DATE_FORMAT)
            date_end = datetime.strptime(date_end, DEFAULT_SERVER_DATE_FORMAT)
            if date_end < date_start:
                date_end = False
                res['value']['effect_to'] = False
                res['value']['month'] = 0
                res['value']['year'] = 0
                res['warning'] = {'title': _('Validation Error!'),
                                  'message': _('Date To must be > Date From !')}
            else:
                res['value']['name'] = datetime.strftime(date_start, '%d/%m/%Y') + '-->' + datetime.strftime(date_end, '%d/%m/%Y')
        if date_end:
            res['value']['month'] = date_end.month
            res['value']['year'] = date_end.year

        return res

    _columns = {
        'code': fields.char(u'Mã timesheet', required=True),
        'name': fields.char(u'Tên timesheet', required=True),
        'description': fields.text(u'Ghi chú'),
        'effect_to': fields.date(u'Ngày kết thúc', required=True),
        'effect_from': fields.date(u'Ngày bắt đầu', required=True),
    }
    _sql_constraints = [
        ('unique_code', 'unique (code)', 'The code of the Timesheet must be unique!')
    ]

    def create(self, cr, uid, vals, context=None):
        timesheet_ids = self.search(cr, uid, [], context=context)
        timesheet_obj = self.browse(cr, uid, timesheet_ids, context=context)

        date_from = datetime.strptime(vals['effect_from'], DEFAULT_SERVER_DATE_FORMAT).date()
        date_to = datetime.strptime(vals['effect_to'], DEFAULT_SERVER_DATE_FORMAT).date()
        for ts_obj in timesheet_obj:

            dh_date_start = datetime.strptime(ts_obj.effect_from, DEFAULT_SERVER_DATE_FORMAT).date()
            dh_date_end = datetime.strptime(ts_obj.effect_to, DEFAULT_SERVER_DATE_FORMAT).date()

            if date_from == dh_date_start or date_from == dh_date_end or date_to == dh_date_start:
                raise Warning(u'Timesheet has been created!')
            elif date_from < dh_date_start:
                if date_to >= dh_date_start:
                    raise Warning(u'Timesheet has been created!')
            else:
                if date_from <= dh_date_end:
                    raise Warning(u'Timesheet has been created!')
        res = super(ts, self).create(cr, uid, vals, context=context)
        return res

class wk_day(osv.osv):
    _name = 'wk.day'
    _columns = {
        'date': fields.date(u'Ngày'),
        'ts_id': fields.many2one('ts', u'Timesheet'),
        'employee_id': fields.many2one('hr.employee',u'Mã NV'),
        'time_in': fields.float(u'Giờ vào'),
        'time_out': fields.float(u'Giờ ra'),
        'total_time': fields.float(u'Tổng giờ làm'),
        'total_time_ot': fields.float(u'Tổng giờ OT')
    }
