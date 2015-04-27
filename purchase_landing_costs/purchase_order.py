# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP s.a. (<http://www.openerp.com>).
#    Copyright (C) 2012-TODAY Mentis d.o.o. (<http://www.mentis.si/openerp>)
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

from osv import osv, fields
import time
from openerp.tools.translate import _

import logging
_logger = logging.getLogger(__name__)

class purchase_order(osv.osv):
    _inherit = "purchase.order"
    _columns = {
        'tipo_cambio': fields.float('Tipo de cambio',digits=(12,6)),
        'landing_costs_line_ids': fields.one2many('purchase.landing.cost.position', 'purchase_order_id', 'Landing Costs'),
     }

    _defaults = {
        'tipo_cambio': 1.0,
    }

    def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, context=None):
        res = super(purchase_order,self)._prepare_order_line_move( cr, uid, order, order_line, picking_id, context)
        res['price_unit_without_costs'] =  res['price_unit']
        res['tipo_cambio'] = order.tipo_cambio
        return res

    def _prepare_order_picking(self, cr, uid, order, context=None):
        res = super(purchase_order,self)._prepare_order_picking( cr, uid, order, context)
        return res

    def _create_pickings(self, cr, uid, order, order_lines, picking_id=False, context=None): 
        res = super(purchase_order,self)._create_pickings(cr, uid, order, order_lines, picking_id, context)
        picking_id = int(res[0])
        landing_cost_object = self.pool.get('purchase.landing.cost.position')
        for order_cost in order.landing_costs_line_ids:
            vals = {}
            vals['product_id'] = order_cost.product_id.id
            vals['partner_id'] = order_cost.partner_id.id
            vals['amount'] = order_cost.amount
            vals['distribution_type'] = order_cost.distribution_type
            vals['picking_id'] = picking_id
            landing_cost_object.create(cr, uid, vals, context=None)

        picking_obj = self.pool.get('stock.picking.in')
        for picking in picking_obj.browse(cr, uid, [picking_id], context=None):
            for line in picking.move_lines:
                for line_cost in line.purchase_line_id.landing_costs_line_ids:
                    vals = {}
                    vals['product_id'] = line_cost.product_id.id
                    vals['partner_id'] = line_cost.partner_id.id
                    vals['amount'] = line_cost.amount
                    vals['distribution_type'] = line_cost.distribution_type
                    vals['move_line_id'] = line.id
                    landing_cost_object.create(cr, uid, vals, context=None) 

        return res

    #AGREGADO EL TIPO DE CAMBIO
    def onchange_pricelist(self, cr, uid, ids, pricelist_id, context=None):
        if not pricelist_id:
            return {}  
        res = {}  
        currency = self.pool.get('product.pricelist').browse(cr, uid, pricelist_id, context=context).currency_id
        get_rate = None
        if 'date' in context:
            date = context['date']
        else:
            date = time.strftime('%Y-%m-%d')
        date = date or time.strftime('%Y-%m-%d')

        if currency.name == 'USD':
            '''
            mod_obj = self.pool.get('res.currency')
            base_currency_ids = mod_obj.search(cr, uid, [('base','=',True)], context=context)
            pen_currency_ids = mod_obj.search(cr, uid, [('name','=','PEN')], context=context)

            get_rate = mod_obj.compute(cr, uid, base_currency_ids[0], pen_currency_ids[0], 1.0,round=False) or 1.0 
            #get_price = mod_obj.read(cr, uid, context)

            #voucher_rate = self.pool.get('res.currency').read(cr, uid, currency.id, ['rate'], context)['rate']      
            '''
            currency_rate_type = 1 #COGE EL TIPO DE CAMBIO DE VENTA
            # ... and use 'is NULL' instead of '= some-id'.
            operator = '=' if currency_rate_type else 'is'
            #SELECT currency_id, rate FROM res_currency_rate WHERE currency_id = 1 AND name <= '2014-11-14' AND currency_rate_type_id =19 ORDER BY name desc LIMIT 1
            id=1
            cr.execute("SELECT currency_id, rate FROM res_currency_rate WHERE currency_id = %s AND name <= %s AND currency_rate_type_id " + operator +" %s ORDER BY name desc LIMIT 1" ,(id, date, currency_rate_type))
            if cr.rowcount:
                id, rate = cr.fetchall()[0]
                res[id] = rate
            else:
                #raise osv.except_osv(_('Error!'),_("No currency rate associated for currency %d for the given period" % (id)))
                cr.execute("SELECT currency_id, rate FROM res_currency_rate WHERE currency_id = %s AND name <= %s  ORDER BY name desc LIMIT 1" ,(id, date,))
                id, rate = cr.fetchall()[0]
                res[id] = rate
                
            get_rate = res[1]
            #_logger.error("SOLES -: %r", rate)
        return {'value': {'currency_id': currency.id, 'tipo_cambio': get_rate or 1  }}

    