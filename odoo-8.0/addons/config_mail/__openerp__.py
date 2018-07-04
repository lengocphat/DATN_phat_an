{
    'name': 'Config Mail',
    'category': 'Hidden',
    'version': '1.0',
    'author': 'Phat',
    'description':
        """
OpenERP Web core module.
========================

This module provides the core of the OpenERP Web Client.
        """,
    'depends': ['base'],
    'auto_install': True,
    'data': [

        'view/config_mail_view.xml',
        'view/menu.xml',
    ],
    'bootstrap': True, # load translations for login screen
}
