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


from openerp.osv import osv,fields
from openerp import netsvc
from openerp.tools.translate import _
import time

from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)

class pos_config(osv.osv):
    _name = 'pos.config'
    _inherit = 'pos.config'
    _columns = {
            'printer_id':fields.many2one('printing.printer','Ticketera'),
            'aut_sunat': fields.char('Codigo autorizacion SUNAT',size=64),
            'n_serie': fields.char('Numero de serie Ticketera',size=64),
            'sequencetb_id': fields.many2one('ir.sequence', "Secuencia Ticket Boleta",),
            'sequencetf_id': fields.many2one('ir.sequence', "Secuencia Ticket Factura",), 
            'footer_ticket': fields.text('Pied de pagina'),

        }

pos_config()


class pos_order(osv.osv):
    _name = 'pos.order'
    _inherit ='pos.order'

    def create_picking(self, cr, uid, ids, context=None):
        """Create a picking for each order and validate it."""
        picking_obj = self.pool.get('stock.picking.out')
        partner_obj = self.pool.get('res.partner')
        move_obj = self.pool.get('stock.move')

        for order in self.browse(cr, uid, ids, context=context):

            ###############PARA AGREGAR EL NUMERO DE TICKET YA SEA FACTURA O BOLETA
            session = self.pool.get('pos.session').browse(cr, uid, order.session_id.id, context)
            config = self.pool.get('pos.config').browse(cr, uid, session.config_id.id, context)
            sequence_obj = self.pool.get('ir.sequence')
            #_logger.error("TICKET SESION: %r", config)
            if config: #AÑADE LA IMPRESION DE SECUENCIA DE FACTURA O BOLETA
                if order.es_factura:
                    values = {'pos_reference': sequence_obj.get_id(cr, uid, config.sequencetf_id.id, context=context)}      
                    #_logger.error("TICKET FACTURA: %r", values)  
                    self.write(cr, uid, [order.id], values, context=context)
                else:
                    values = {'pos_reference': sequence_obj.get_id(cr, uid, config.sequencetb_id.id, context=context)}   
                    #_logger.error("TICKET BOLETA: %r", values)     
                    self.write(cr, uid, [order.id], values, context=context)
            ###########FIN#########################3

            addr = order.partner_id and partner_obj.address_get(cr, uid, [order.partner_id.id], ['delivery']) or {}
            if order.almacendespacho_id:
                if order.partner_id:
                    destination_id = order.partner_id.property_stock_customer.id 
                else:
                    destination_id = partner_obj.default_get(cr, uid, ['property_stock_customer'], context=context)['property_stock_customer']
                uid=1 
                picking_id = picking_obj.create(cr, uid, {
                    'origin': order.name,
                    'partner_id': addr.get('delivery',False),
                    #'type': 'in' if order.devolucion else 'out',
                    'type': 'out',                
                    'company_id': order.company_id.id,
                    'move_type': 'direct',
                    'note': order.note or "",
                    'invoice_state': 'none',
                    'auto_picking': False,
                    'location_id': order.almacendespacho_id.id,
                    'location_dest_id': destination_id,
                    'state': 'auto',                    
                }, context=context)
                self.write(cr, uid, [order.id], {'picking_id': picking_id}, context=context)
                location_id = order.almacendespacho_id.id           

                for line in order.lines:
                    if line.product_id and line.product_id.type == 'service':
                        continue
                    move_obj.create(cr, uid, {
                        'name': line.name,
                        'product_uom': line.product_id.uom_id.id,
                        'product_uos': line.product_id.uom_id.id,
                        'picking_id': picking_id,
                        'product_id': line.product_id.id,
                        'product_uos_qty': abs(line.qty),
                        'product_qty': abs(line.qty),
                        'tracking_id': False,
                        #'type': 'in' if order.devolucion else 'out', 
                        'type': 'out', 
                        'state': 'draft',
                        'location_id': location_id if line.qty >= 0 else destination_id,
                        'location_dest_id': destination_id if line.qty >= 0 else location_id,
                        'date_expected': order.fecha_expected or order.date_order,#PARA ESPECIFICAR UNA FEHCA DE ENTREGA EN EL ALMACEN
                    }, context=context)
                wf_service = netsvc.LocalService("workflow")
                wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
                #picking_obj.force_assign(cr, uid, [picking_id], context)
                picking_obj.action_assign(cr, uid, [picking_id], context)

                
            else:
                if order.partner_id:
                    destination_id = order.partner_id.property_stock_customer.id 
                else:
                    destination_id = partner_obj.default_get(cr, uid, ['property_stock_customer'], context=context)['property_stock_customer'] 

                picking_id = picking_obj.create(cr, uid, {
                    'origin': order.name,
                    'partner_id': addr.get('delivery',False),
                    #'type': 'in' if order.devolucion else 'out', 
                    'type': 'out', 
                    'company_id': order.company_id.id,
                    'move_type': 'direct',
                    'note': order.note or "",
                    'invoice_state': 'none',
                    'auto_picking': True,
                    #'location_id': order.shop_id.warehouse_id.lot_stock_id.id if not order.devolucion else destination_id,
                    'location_id': order.shop_id.warehouse_id.lot_stock_id.id,
                    #'location_dest_id': destination_id if not order.devolucion else order.shop_id.warehouse_id.lot_stock_id.id,
                    'location_dest_id': destination_id,
                }, context=context)
                self.write(cr, uid, [order.id], {'picking_id': picking_id}, context=context)
                location_id = order.shop_id.warehouse_id.lot_stock_id.id            

                for line in order.lines:
                    if line.product_id and line.product_id.type == 'service':
                        continue
                    move_obj.create(cr, uid, {
                        'name': line.name,
                        'product_uom': line.product_id.uom_id.id,
                        'product_uos': line.product_id.uom_id.id,
                        'picking_id': picking_id,
                        'product_id': line.product_id.id,
                        'product_uos_qty': abs(line.qty),
                        'product_qty': abs(line.qty),
                        'tracking_id': False,
                        #'type': 'in' if order.devolucion else 'out', 
                        'type': 'out', 
                        'state': 'draft',
                        'location_id': location_id if line.qty >= 0 else destination_id,
                        'location_dest_id': destination_id if line.qty >= 0 else location_id,
                    }, context=context)
                wf_service = netsvc.LocalService("workflow")
                wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
                picking_obj.force_assign(cr, uid, [picking_id], context)

            

        return True



