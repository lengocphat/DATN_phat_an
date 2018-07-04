# -*- coding: utf-8 -*-
import logging
from openerp.osv import osv, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
from xlrd import open_workbook
import base64
import thread
from threading import Thread
import datetime
import xlrd
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import codecs
import datetime, xlrd
from datetime import datetime
from openerp.exceptions import Warning
import smtplib
from email.mime.text import MIMEText

class leave(osv.osv):
    _name = 'leave'
    _rec_name = 'name'

    # def get_sign_in_emp_id(self, cr, uid, ids, name, args, context=None):
    #     res = {}
    #     resource_obj = self.pool.get('resource.resource')
    #     resource_id = resource_obj.search(cr, uid, [('user_id', '=', uid)], context=None)
    #     emp_id = self.pool.get('hr.employee').search(cr, uid, [('resource_id','=',resource_id[0])], context=None)
    #     for row in self.browse(cr,uid,ids,context=None):
    #         emp_id1 = row.employee_id.id
    #         if emp_id[0] == emp_id1:
    #             res[row.id] = True
    #         else:
    #             res[row.id] = False
    #     return res

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        if user != 1:
            resource_obj = self.pool.get('resource.resource')
            resource_id = resource_obj.search(cr, user, [('user_id', '=', user)], context=None)
            if not resource_id:
                raise Warning(u'This account does not have employee information')
            employee_obj = self.pool.get('hr.employee')
            employee_ids = employee_obj.search(cr, user, [('resource_id', '=', resource_id[0])], context=None)
            # employee = employee_obj.browse(cr, user, employee_id, context=None)
            group_obj = self.pool.get('res.groups')
            group_manager = group_obj.browse(cr, user, 12, context=None)
            for a_user in group_manager.users:
                if a_user.id == user:
                    return super(leave, self).search(cr, user, args,  offset=0, limit=None, order=None, context=None, count=False)
            args += [('employee_id', '=', employee_ids[0])]
        return super(leave, self).search(cr, user, args,  offset=0, limit=None, order=None, context=None, count=False)

    _columns = {
        'employee_id': fields.many2one('hr.employee',u'Tên nhân viên'),
        'name': fields.char(u'Mã'),
        'leave_type_id': fields.many2one('leave.type', string=u'Loại nghỉ', required=True),
        'total_day_leave_type': fields.integer(string=u'Số ngày nghỉ tối đa'),
        'day_off_left': fields.integer(u'Số ngày được phép nghỉ còn lại'),
        'day_off': fields.char(u'Số ngày đã nghỉ'),
        'reason': fields.char(u'Lí do nghỉ', required=True),
        'date_from': fields.date(u'Từ ngày', required=True),
        'date_to': fields.date(u'Đến ngày', required=True),
        'description_leave': fields.text(readonly=True),
        'total_day': fields.integer(u'Số ngày nghỉ'),
        'stage': fields.selection([('draft','Draft'), ('waiting','Waiting HRM'), ('approved','Approved'), ('cancelled','Cancelled')], string='Stage', default='draft'),
        # 'sign_in_emp_id': fields.function(get_sign_in_emp_id, string='a', type='boolean')
    }

    def convert_day(seff, str):
        flag = datetime.strptime(str, '%Y-%m-%d')
        str = datetime.strftime(flag, '%d-%m-%Y')
        return str

    def send_mail(self, email_from, password, email_to, msg):
        smtpObj = smtplib.SMTP(host='smtp.gmail.com', port=587)
        smtpObj.ehlo()
        smtpObj.starttls()
        smtpObj.ehlo()
        smtpObj.login(user=email_from, password=password)
        smtpObj.sendmail(email_from, email_to, msg)

    def change_stage(self, cr, uid, id, status):
        leave = self.browse(cr, uid, id)
        if leave.employee_id.work_email:
            mail_id = self.pool.get('config.mail').search(cr, 1, [])
            mail = self.pool.get('config.mail').browse(cr, 1, mail_id)
            if mail[len(mail_id)-1]:
                resource_obj = self.pool.get('resource.resource')
                resource_id = resource_obj.search(cr, uid, [('user_id', '=', uid)], context=None)
                employee_obj = self.pool.get('hr.employee')
                employee_id = employee_obj.search(cr, uid, [('resource_id', '=', resource_id[0])], context=None)
                employee = employee_obj.browse(cr, uid, employee_id[0], context=None)
                receivers = str(leave.employee_id.work_email)
                header = '''From: %s\r\nTo: %s\r\nSubject: Xác nhận nghỉ phép\r\n\r\n''' % (mail[len(mail_id)-1].user_name.encode('utf-8', 'replace'),
                                                                                            receivers.encode('utf-8', 'replace'))
                message = '''Chào %s 
%s đã %s đơn xin nghỉ phép của bạn.
Thời gian: Từ ngày %s đến ngày %s.
Số ngày nghỉ: %s.
Lý do: %s.
Loại nghỉ: %s.
                    ''' % (leave.employee_id.name.encode('utf-8', 'replace'), employee.name.encode('utf-8', 'replace'), status.encode('utf-8', 'replace'),
                           self.convert_day(leave.date_from).encode('utf-8', 'replace'), self.convert_day(leave.date_to).encode('utf-8', 'replace'),str(leave.total_day).encode('utf-8', 'replace'),
                           leave.reason.encode('utf-8', 'replace'), leave.leave_type_id.name.encode('utf-8', 'replace'))
                msg = header + message
                self.send_mail(mail[len(mail_id)-1].user_name, mail[len(mail_id)-1].password, receivers, msg)
            else:
                raise Warning(u'You have not config company email yet!!!')

    def set_leave_waiting(self, cr, uid, ids, context=None):
        for leaves in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, [leaves.id], {'stage': 'waiting'}, context=context)
        return True

    def set_leave_approved(self, cr, uid, ids, context=None):
        for leaves in self.browse(cr, uid, ids, context=context):
            self.change_stage(cr, uid, [leaves.id], u'duyệt')
            self.write(cr, uid, [leaves.id], {'stage': 'approved'}, context=context)
        return True

    def set_leave_cancelled(self, cr, uid, ids, context=None):
        for leaves in self.browse(cr, uid, ids, context=context):
            self.change_stage(cr, uid, [leaves.id], u'hủy')
            self.write(cr, uid, [leaves.id], {'stage': 'cancelled'}, context=context)
        return True

    def create(self, cr, uid, vals, context=None):
        if vals['total_day'] > vals['day_off_left']:
            raise Warning(u"Exceeded number of days allowed")
        else:
            resource_obj = self.pool.get('resource.resource')
            resource_id = resource_obj.search(cr, uid, [('user_id', '=', uid)], context=None)
            employee_obj = self.pool.get('hr.employee')
            employee_id = employee_obj.search(cr, uid, [('resource_id', '=', resource_id[0])], context=None)
            employee = employee_obj.browse(cr, uid, employee_id, context=None)

            vals['employee_id'] = employee.id
            vals['stage'] = 'waiting'
            leave_type_id = vals.get('leave_type_id')
            leave_type_obj = self.pool.get('leave.type').browse(cr, uid, leave_type_id)
            leave_obj = self.pool.get('leave')
            leaves_id = leave_obj.search(cr, uid, [('employee_id', '=', employee.id),('leave_type_id', '=', leave_type_id),('stage', '=', 'waiting')])
            if leaves_id:
                raise Warning(u'You have a leave request waiting for approval')
            leaves_id = leave_obj.search(cr, uid, [('employee_id', '=', employee.id),('stage','in',('waiting','approved'))])

            date_from = datetime.strptime(vals['date_from'], DEFAULT_SERVER_DATE_FORMAT).date()
            date_to = datetime.strptime(vals['date_to'], DEFAULT_SERVER_DATE_FORMAT).date()
            for id in leaves_id:
                row = leave_obj.browse(cr, uid, id)

                dh_date_start = datetime.strptime(row.date_from, DEFAULT_SERVER_DATE_FORMAT).date()
                dh_date_end = datetime.strptime(row.date_to, DEFAULT_SERVER_DATE_FORMAT).date()

                if date_from == dh_date_start or date_from == dh_date_end or date_to == dh_date_start:
                    raise Warning(u'This day is requested for leave!')
                elif date_from < dh_date_start:
                    if date_to >= dh_date_start:
                        raise Warning(u'This day is requested for leave!')
                else:
                    if date_from <= dh_date_end:
                        raise Warning(u'This day is requested for leave!')
            print vals
            list_leave = self.search(cr, uid, [])
            vals['name'] = str(len(list_leave)) + '_' + leave_type_obj.code + '_' + str(vals['employee_id'])
            leave_id = super(leave, self).create(cr, uid, vals, context=context)
            return leave_id

    def write(self, cr, uid, ids, vals, context=None):
        leave_obj = self.pool.get('leave')
        resource_obj = self.pool.get('resource.resource')
        employee_obj = self.pool.get('hr.employee')
        leaves = self.browse(cr, uid, ids, context=None)
        if leaves.total_day > leaves.day_off_left:
            raise Warning(u"Exceeded number of days allowed")
        else:
            # resource_id = employee_obj.search(cr, uid, [('id', '=', leaves.employee_id.id)], context=None)
            # resource = resource_obj.browse(cr, uid, resource_id, context=None)
            #
            # employee = employee_obj.browse(cr, uid, employee_id, context=None)

            leave_type_id = vals.get('leave_type_id')
            leaves_id = leave_obj.search(cr, uid,
                                         [('employee_id', '=', leaves.employee_id.id), ('leave_type_id', '=', leave_type_id),
                                          ('stage', '!=', 'approved')])
            if leaves_id:
                raise Warning(u'You have a leave request waiting for approval')

            name = str(ids[0]) + '_' + leaves.leave_type_id.code
            vals['name'] = name
            return super(leave, self).write(cr, uid, ids, vals, context=context)

    def onchange_leave_type(self, cr, uid, ids, leave_type_id):
        leave_type_obj = self.pool.get('leave.type').browse(cr, uid, leave_type_id)
        res = {}
        if leave_type_obj:
            res['value'] = {}
            res['value']['total_day_leave_type'] = leave_type_obj.day_off_allowed
            res['value']['description_leave'] = leave_type_obj.description
            resource_obj = self.pool.get('resource.resource')
            resource_id = resource_obj.search(cr, uid, [('user_id', '=', uid)] , context=None)
            if not resource_id:
                raise Warning(u'This account does not have employee information!')
            employee_obj = self.pool.get('hr.employee')
            employee = employee_obj.search(cr, uid, [('resource_id', '=', resource_id[0])], context=None)
            if not employee:
                raise Warning(u'This account does not have employee information!')
            leave_list = self.search(cr, uid, [('employee_id', '=', employee[0]), ('leave_type_id', '=', leave_type_id), ('stage', '=', 'approved')])
            total = 0
            day_off_left = 0
            for i in self.browse(cr, uid, leave_list):
                if i.total_day:
                    total = total + i.total_day
            day_off_left = leave_type_obj.day_off_allowed - total
            res['value']['day_off'] = str(total)
            res['value']['day_off_left'] = day_off_left

        return res

    def date_onchange(self,cr, uid, ids, date_start, date_end, context=None):
        res = {'value': {'name': '', 'month': 0, 'year': 0}, 'warning': {}}

        if date_start and date_end:
            date_start = datetime.strptime(date_start, DEFAULT_SERVER_DATE_FORMAT)
            date_end = datetime.strptime(date_end, DEFAULT_SERVER_DATE_FORMAT)
            if date_end < date_start:
                date_end = False
                res['value']['date_to'] = False
                res['value']['month'] = 0
                res['value']['year'] = 0
                res['warning'] = {'title': _('Validation Error!'),
                                  'message': _('Date To must be > Date From !')}
            else:
                flag = date_end - date_start
                if flag.days >= 0:
                    res['value']['total_day'] = flag.days + 1
                else:
                    raise Warning(u"Invalid date input!!!")
        if date_end:
            res['value']['month'] = date_end.month
            res['value']['year'] = date_end.year

        return res

class leave_type(osv.osv):
    _name = 'leave.type'
    _rec_name = 'name'
    _columns = {
        'name': fields.char(u'Loại nghỉ', required=True),
        'day_off_allowed': fields.integer(u'Số ngày phép được nghỉ', required=True),
        'description': fields.text(u'Ghi chú', required=True),
        'code': fields.char(u'Mã loại nghỉ', required=True),
    }

