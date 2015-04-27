# -*- encoding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (c) 2014 KIDDYS HOUSE SAC. (http://kiddyshouse.com).
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
    "name" : "Pos extend",
    "version" : "0.1",
    "author" : "Ing. Javier Salazar Carlos",
    "description" : """
                    Extiende las funcionalidades del punto de venta.
                    - Permite hacer pedido de distintos almacenes
                    """,
    "website" : "http://salazarcarlos.com",
    "depends" : ["base", "stock",'point_of_sale','sale','product_attribute','product_qty_disponible','sale_multishop','account'],
    "data" : [
            'security/pos_extend_security.xml',
            'pos_extend_view.xml',
            'pos_order_report.xml',	        
	        'wizard/pos_payment.xml',
    ],
    "demo_xml" : [
    ],
    "update_xml" : [
            'pos_extend_view.xml',
    ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: