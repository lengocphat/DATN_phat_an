# -*- coding: utf-8 -*-
from openerp.osv import osv, fields
import logging
from openerp import tools

log = logging.getLogger(__name__)

class etalk_security_scan_group(osv.osv):
    _name = "etalk.security.scan.group"
    _auto = False
    _order = 'name'
    
    _columns = {
                'name' : fields.many2one('ir.model', 'Object'),
                'perm_read' : fields.boolean('Perm Read'),
                'perm_write' : fields.boolean('Perm Write'),
                'perm_create' : fields.boolean('Perm Create'),
                'perm_unlink' : fields.boolean('Perm Unlink'),
                'module' : fields.char('Module'),
                'group' : fields.many2one('res.groups', 'Group')
                }
    
    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'etalk_security_scan_group')
        cr.execute("""
            create or replace view etalk_security_scan_group as (
                select row_number() over (partition by 1) as id, im.id as name, rg.id as group, ima.perm_read as perm_read, 
                        ima.perm_write as perm_write, ima.perm_create as perm_create, ima.perm_unlink as perm_unlink,
                        imd.module as module
                    from etalk_security_exception vse
                        inner join ir_model im on im.id=vse.name 
                        inner join ir_model_access ima on ima.model_id=im.id 
                        left join res_groups rg on rg.id=ima.group_id
                        left join ir_model_data imd on (imd.res_id = rg.id and imd.model = 'res.groups')
                        left join etalk_exception_group_rel vser on vser.group_id=rg.id 
                    where (ima.perm_read<>vse.perm_read
                        or ima.perm_write<>vse.perm_write 
                        or ima.perm_create<>vse.perm_create
                        or ima.perm_unlink<>vse.perm_unlink)
                        and vser.group_id is null
                    group by 2,3,4,5,6,7,8
            )
        """)
    
etalk_security_scan_group()

