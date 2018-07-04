# -*- coding: utf-8 -*-
from openerp.osv import osv, fields
import logging

log = logging.getLogger(__name__)

class etalk_security_exception(osv.osv):
    _name = "etalk.security.exception"
    
    _columns = {
                'name' : fields.many2one('ir.model', 'Object', required = True),
                'perm_read' : fields.boolean('Perm Read'),
                'perm_write' : fields.boolean('Perm Write'),
                'perm_create' : fields.boolean('Perm Create'),
                'perm_unlink' : fields.boolean('Perm Unlink'),
                'active' : fields.boolean('Active'),
                'groups' : fields.many2many('res.groups', 'etalk_exception_group_rel','exception_id', 'group_id','Group')
                }
    
    _defaults = {
                 'active' : True,
                 }
etalk_security_exception()

