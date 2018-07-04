{
    'name': 'Leave',
    'category': 'Hidden',
    'version': '1.0',
    'author': 'Phat',
    'description':
        """
OpenERP Web core module.
========================

This module provides the core of the OpenERP Web Client.
        """,
    'depends': ['base', 'hr'],
    'auto_install': True,
    'data': [
        'views/leave.xml',
        'views/leave_type_views.xml',
    ],
    'bootstrap': True, # load translations for login screen
}
