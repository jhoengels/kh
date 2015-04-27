# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) KIDDYS HOUSE S.A.C (<http://kiddyshouse.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time

from osv import fields, osv
from tools.translate import _
import decimal_precision as dp
from product._common import rounding
import netsvc

import logging
_logger = logging.getLogger(__name__)




class sale_order(osv.osv):
    _inherit = "sale.order"

    _columns = {
        'fecha_expected': fields.datetime('Fecha entrega al cliente', required=False, readonly=False, select=True, states={'draft': [('readonly', False)]}),
        'canal_venta': fields.selection([('01','Venta Tienda'),('02',' Venta de Campo'),('03','Venta por Telefono'),('04','Venta por Correo'),('05','Venta de Facebook')],'Canal de venta',required=False,),
    }
    def _prepare_order_line_move(self, cr, uid, order, line, picking_id, date_planned, context=None):
        location_id = order.shop_id.warehouse_id.lot_stock_id.id
        output_id = order.shop_id.warehouse_id.lot_output_id.id

        return {
            'name': line.name,
            'picking_id': picking_id,
            'product_id': line.product_id.id,
            'date': date_planned,
            #'date_expected': date_planned,
            'date_expected': order.fecha_expected or date_planned,##Añadir dependencia(sale_stock) porque de eso hereda este metodo
            'product_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'product_uos_qty': (line.product_uos and line.product_uos_qty) or line.product_uom_qty,
            'product_uos': (line.product_uos and line.product_uos.id) or line.product_uom.id,
            'product_packaging': line.product_packaging.id,
            'partner_id': line.address_allotment_id.id or order.partner_shipping_id.id,
            'location_id': location_id,
            'location_dest_id': output_id,
            'sale_line_id': line.id,
            'tracking_id': False,
            'state': 'draft',
            #'state': 'waiting',
            'company_id': order.company_id.id,
            'price_unit': line.product_id.standard_price or 0.0
        }


sale_order() 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
