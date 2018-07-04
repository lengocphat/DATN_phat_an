# -*-coding:utf-8-*-
import logging
from openerp.osv import osv, fields
from xlrd import open_workbook
from openerp.tools.translate import _
from openerp.tools import html2text
import openerp.tools as tools
import datetime, xlrd
from openerp.exceptions import Warning
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
from datetime import datetime

class config_mail(osv.osv):
    _inherit = 'res.config.settings'
    _name = 'config.mail'

    def get_default_values(self, cr, uid, ids, fields, context=None):
        last_rec_query = "SELECT * FROM config_mail ORDER BY create_date DESC LIMIT 1"
        cr.execute(last_rec_query)
        last_rec = cr.dictfetchone()
        return {
            'user_name': last_rec.get('user_name', '') if last_rec else '',
            'password': last_rec.get('password') if last_rec else '',
            'security': last_rec.get('security', '') if last_rec else '',
        }

    _columns = {
        'user_name': fields.char('User name', required=True),
        'password': fields.char('Password', required=True),
        'security': fields.selection([('ssl', 'SSL/TLS')], string='Connection Security', required=True),
    }
    def test(self, cr, uid, ids, context=None):
        last_rec_query = "SELECT * FROM config_mail ORDER BY create_date DESC LIMIT 1"
        cr.execute(last_rec_query)
        last_rec = cr.dictfetchone()
        if last_rec:
            mail = self.pool.get('ir.mail_server')
            smtp = False
            try:
                smtp = mail.connect('smtp.gmail.com', 465, user=last_rec['user_name'],
                                    password=last_rec['password'], encryption=last_rec['security'],
                                    smtp_debug=False)
            except Exception, e:
                raise osv.except_osv(_("Connection Test Failed!"),
                                     _("Here is what we got instead:\n %s") % tools.ustr(e))
            finally:
                try:
                    if smtp: smtp.quit()
                except Exception:
                    # ignored, just a consequence of the previous exception
                    pass
        raise osv.except_osv(_("Connection Test Succeeded!"), _("Everything seems properly set up!"))

