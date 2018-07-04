# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Trobz (trobz.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Excel 2007+ report engine',
    'version': '0.4',
    'license': 'AGPL-3',
    'author': 'Trobz',
    'website': 'http://trobz.com',
    'category': 'Reporting',
    'description': """
Excel report engine
===================

This module adds Excel (.xlsx) export capabilities to the standard OpenERP reporting engine.

Report development
''''''''''''''''''
In order to create an Excel report you can\n
- define a report of type 'xlsx'
- pass ``{'xlsx_export': 1}`` via the context to the report create method

The ``report_xlsx`` class contains a number of attributes and methods to facilitate
the creation XLSX reports in OpenERP.

* cell types

  Supported cell types : text, number, boolean, date.

* cell styles

  The predefined cell style definitions result in a consistent
  look and feel of the OpenERP Excel reports.

    """,
    'depends': ['base'],
    # 'external_dependencies': {'python': ['xlsxwriter']},
    'demo': [],
    'data': [],
    'active': False,
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
