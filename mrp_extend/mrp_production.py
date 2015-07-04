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

from osv import fields, osv
import openerp.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)

class stock_location(osv.osv):
    _inherit ='stock.location'
    _columns = {
        'sequence_production_id': fields.many2one('ir.sequence', "Secuencia de fabricacion", help="Secuencia utilizada para las ordenes de fabricacion de productos."), 
    }   
class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    _columns = {
        'name': fields.char('Reference', size=64, required=True, readonly=True,),
    }
    _defaults = {
        'name':  '/',
    }    

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}           
        production_id = super(mrp_production, self).create(cr, uid, vals, context=context)        
        location_id = vals.get('location_src_id', [])
        #_logger.error("INNNNNN111111: %r", location_id)
        location = self.pool.get('stock.location').browse(cr, uid, location_id, context)
        sequence_obj = self.pool.get('ir.sequence')

        if location.sequence_production_id:
            vals = {'name': sequence_obj.get_id(cr, uid, location.sequence_production_id.id, context=context)}
            self.write(cr, uid, [production_id], vals, context=context)
        else:
            raise osv.except_osv(_('Error!'),_('El almacen no tiene asignado Secuencia de fabricacion'))
            
        return production_id   

    def action_production_end(self, cr, uid, ids, context=None):

        write_res = super(mrp_production, self).action_production_end(cr, uid, ids, context) 
        if write_res:
            for production in self.pool.get('mrp.production').browse(cr, uid, ids, context=None):
                product_id = production.product_id.id
                
                product_obj=self.pool.get('product.product')
                stock_obj=self.pool.get('stock.move')

                if production.product_id.cost_method == 'average' :

                    new_standard_price = 0.0

                    for line in production.bom_id.bom_lines:
                        new_standard_price += line.product_id.standard_price*line.product_qty
                    new_standard_price_final = new_standard_price + production.bom_id.mod + production.bom_id.cif/100.00*production.product_id.list_price    
                    
                    #Actualizando el PRECIO promedio del producto a fabricar

                    product = product_obj.browse(cr, uid, [product_id], context)[0]
                    if (product.qty_available-production.product_qty)<=0:
                        product_obj.write(cr, uid, [product_id], {'standard_price': new_standard_price_final}, context)
                    else: 
                        new_price_promedio = ((product.qty_available-production.product_qty)*product.standard_price + production.product_qty*new_standard_price_final)/(product.qty_available)                        
                        product_obj.write(cr, uid, [product_id], {'standard_price': new_price_promedio}, context)    
                    #Fin actualizar PRECIO

                    #Actualiza el price_unit del mov. en stock.move del producto consumido
                    for move in production.move_lines2:
                        stock_obj.write(cr, uid, move.id, {'price_unit': move.product_id.standard_price}, context)
                        #_logger.error("COTIZACION 1---: %r", move.name )
                    #Actualiza el price_unit del mov. en stock.move del producto producido
                    for move in production.move_created_ids2:
                        stock_obj.write(cr, uid, move.id, {'price_unit': new_standard_price_final}, context)

        return write_res

class mrp_bom(osv.osv):
    _inherit= 'mrp.bom'
    _columns = {
        'mod': fields.float('Mano de obra directa',digits=(2,1)),
        'cif': fields.float('Costos inderectos de fabricacion',digits=(2,1)), 
        'product_qty': fields.float('Product Quantity', required=True, digits_compute=dp.get_precision('PrecioCompra')),   
    }

        