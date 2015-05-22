# -*- encoding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (c) 2015 S&C. (http://salazarcarlos.com).
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name" : "Product Composition",
    "version" : "0.1",
    "author" : "Ing. Javier Salazar Carlos",
    "description" : """
                    Hace que un producto pueda estar compuesta por otros productos.
                    """,
    "website" : "http://salazarcarlos.com",
    "depends" : ["base", "stock", 'product','location_sequences'],
    "data" : [
            'product_view.xml',
            'composition_sequence.xml',
            'location_data.xml',
            'security/security.xml',
	        'security/ir.model.access.csv',
    ],
    "demo_xml" : [
    ],
    "update_xml" : [
            'product_view.xml',
    ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: