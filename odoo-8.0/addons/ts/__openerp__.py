{
    'name': 'Time Sheet',
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
        'ts_views.xml',
        'working_day_views.xml',
        'wk_day_import_views.xml'
    ],
    'bootstrap': True, # load translations for login screen
}
