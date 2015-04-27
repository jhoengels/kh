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

class stock_partial_picking(osv.osv_memory):
    _inherit = "stock.partial.picking"

    def _product_cost_for_average_update(self, cr, uid, move):
        res = super(stock_partial_picking, self)._product_cost_for_average_update(cr, uid, move)       
        res['cost'] = move.price_unit_without_costs
        return res
    

class stock_invoice_onshipping(osv.osv_memory):
    _inherit = "stock.invoice.onshipping"

    _columns = {
        'tipo_cambio': fields.float('Tipo de cambio',digits=(12,6),help="Tipo de cambio a la fecha de emision de la factura"),
     }
    _defaults = {
        'tipo_cambio' : 1,
    }


    def create_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        picking_pool = self.pool.get('stock.picking')
        onshipdata_obj = self.read(cr, uid, ids, ['journal_id', 'group', 'invoice_date','tipo_cambio'])

        if context.get('new_picking', False):
            onshipdata_obj['id'] = onshipdata_obj.new_picking
            onshipdata_obj[ids] = onshipdata_obj.new_picking
        context['date_inv'] = onshipdata_obj[0]['invoice_date']
        active_ids = context.get('active_ids', [])
        
        for picking in picking_pool.browse(cr, uid, active_ids, context=context):
            for move_line in picking.move_lines:
                self.pool.get('stock.move').write(cr, uid, [move_line.id], {'tipo_cambio': onshipdata_obj[0]['tipo_cambio']}, context=context)


        active_picking = picking_pool.browse(cr, uid, context.get('active_id',False), context=context)

        inv_type = picking_pool._get_invoice_type(active_picking)
        context['inv_type'] = inv_type
        if isinstance(onshipdata_obj[0]['journal_id'], tuple):
            onshipdata_obj[0]['journal_id'] = onshipdata_obj[0]['journal_id'][0]        

        res = picking_pool.action_invoice_create(cr, uid, active_ids,
              journal_id = onshipdata_obj[0]['journal_id'],
              group = onshipdata_obj[0]['group'],
              type = inv_type,
              context=context)
        return res