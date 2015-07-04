# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 S&C (<http://salazarcarlos.com>).
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



from openerp.osv import osv,fields,orm
from openerp import netsvc
from openerp.tools.translate import _
import time
from openerp import tools

from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

from openerp import SUPERUSER_ID

class stock_max_min_line(orm.Model):
    _name = 'stock.max.min.line'
    _columns = {
        'name': fields.char('Nombre'),
        'product_id': fields.many2one('product.product', 'Producto', required=True, ),
        'stock_min': fields.float('Cantidad minima', digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
        'stock_max': fields.float('Cantidad maxima', digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
        'max_min_id': fields.many2one('stock.max.min', 'Stock max min',  ondelete='cascade'),
    }
    _defaults = {
        'stock_min': lambda obj, cr, uid, context: 0.0,
        'stock_max': lambda obj, cr, uid, context: 0.0,  
   }

    def create(self, cr, uid, vals, context=None):
        res_id = super(stock_max_min_line, self).create(cr, uid, vals, context)
        if ('product_id' in vals):
            prod = self.pool.get('product.product').browse(cr, uid, vals['product_id'], context=context)
            vals.update({'name': prod.name })
        self.write(cr, uid, [res_id], vals, context=context)        
        return res_id

    def write(self, cr, uid, ids, vals, context=None):
        #_logger.error("INNNNNN111111: %r", vals)
        if ('product_id' in vals):
            prod = self.pool.get('product.product').browse(cr, uid, vals['product_id'], context=context)
            vals.update({'name': prod.name })
        return super(stock_max_min_line, self).write(cr, uid, ids, vals, context=context)  

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        return super(stock_max_min_line, self).search(cr, uid, args, offset, limit, order, context, count)    
    #Eliminar un registro
    def unlink(self, cr, uid, ids, context=None):
        for reg in self.browse(cr, uid, ids, context=context):
            orderpoint_obj = self.pool.get('stock.warehouse.orderpoint')
            orderpoint_id = orderpoint_obj.search(cr, uid,[('warehouse_id','=',reg.max_min_id.warehouse_id.id),('product_id','=',reg.product_id.id)], context=context)
            _logger.error("INNNNNN: %r", orderpoint_id)
            orderpoint_obj.unlink(cr,uid,orderpoint_id,context)
        return super(stock_max_min_line, self).unlink(cr, uid, ids, context=context)      

class stock_max_min(osv.osv):
    _name = 'stock.max.min'
    _columns = {
        'name': fields.char('Nombre', required=True, states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
        'descripcion': fields.char('Descripcion',),
        'user_id': fields.many2one('res.users', 'Usuario', select=True, track_visibility='onchange'), 
        'warehouse_id': fields.many2one('stock.warehouse', 'Almacen', required=True, states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
        'date': fields.datetime('Fecha creacion', required=True, select=1, states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
        'max_min_line_ids': fields.one2many('stock.max.min.line', 'max_min_id', 'Stock Max Min de Productos', states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
        'state': fields.selection([('draft','Vigente'),('done','Obsoleto'),('cancel','Cancelado')],string='Estado',readonly=True,required=True),
    }
    _order='date desc'

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'state': 'draft',
        'user_id': lambda obj, cr, uid, context: uid,        
   }

    def create(self, cr, uid, vals, context=None):
        return super(stock_max_min, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        return super(stock_max_min, self).write(cr, uid, ids, vals, context)    

    def importar_producto(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        stock_max_min_line_obj = self.pool.get('stock.max.min.line')
        product_obj = self.pool.get('product.product')
        datas = {}
        prod_ids = product_obj.search(cr, uid, [], context=context)
        
        for stock_max in self.browse(cr, uid, ids, context=context):
            if stock_max.max_min_line_ids:
                for id in prod_ids:
                    prod_max_min_line_ids = stock_max_min_line_obj.search(cr, uid, [('product_id','=',id)], context=context)
                    if not prod_max_min_line_ids:
                        max_min_line = { 'product_id': id, 'max_min_id': stock_max.id }
                        stock_max_min_line_obj.create(cr, uid, max_min_line)
            else:
                for id in prod_ids:
                    max_min_line = { 'product_id': id, 'max_min_id': stock_max.id }
                    stock_max_min_line_obj.create(cr, uid, max_min_line)                
        return True

    def button_obsoleto(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, { 'state' : 'done' })
        return True

    def button_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, { 'state' : 'cancel' })
        return True    

    def _max_min_line(self, cr, uid, stock_max, line_max_min, context=None):
        max_min_line = { 
            'product_id': line_max_min.product_id.id, 
            'product_uom': line_max_min.product_id.uom_id.id,
            'warehouse_id': stock_max.warehouse_id.id,
            'location_id': stock_max.warehouse_id.lot_stock_id.id,
            'product_min_qty': line_max_min.stock_min,
            'product_max_qty': line_max_min.stock_max,
        }         
        return max_min_line

    def generar_stock_max_min(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        #VERIFICA QUE NO HAYA PRODUCTOS REPETIDOS
        product_obj = self.pool.get('product.product')
        sql = "SELECT product_id, COUNT (product_id) FROM stock_max_min_line WHERE max_min_id=%s GROUP BY product_id ORDER BY COUNT DESC"
        cr.execute(sql, (ids[0],))
        res = cr.fetchall()
        for l  in res:
            if l[1] >1:
                product = product_obj.browse(cr, uid, [l[0]], context)[0]
                raise osv.except_osv(_('Error!'),_('El stock del %s se esta repitiendo') %(product.name))
        #FIN

        orderpoint_obj = self.pool.get('stock.warehouse.orderpoint')
        for stock_max in self.browse(cr, uid, ids, context=context):
            #if stock_max.max_min_line_ids:
            for line_max_min in stock_max.max_min_line_ids:
                prod_max_min_line_ids = orderpoint_obj.search(cr, uid, [('product_id','=',line_max_min.product_id.id),('warehouse_id','=',stock_max.warehouse_id.id)], context=context)
                prod_max_min_line_id = orderpoint_obj.browse(cr, uid, prod_max_min_line_ids, context=context)
                if prod_max_min_line_ids:                                            
                    for val in prod_max_min_line_id:
                        if line_max_min.stock_min > line_max_min.stock_max:
                            raise osv.except_osv(_('Error!'),_('El stock Minimo no puede ser mayor que el stock Maximo, producto "%s"') %(line_max_min.product_id.name))
                        if val.product_min_qty != line_max_min.stock_min or val.product_max_qty != line_max_min.stock_max:
                            res = self._max_min_line(cr, uid, stock_max, line_max_min, context)
                            #_logger.error("INNNNNN: %r", res)
                            orderpoint_obj.write(cr, uid, prod_max_min_line_ids, res)
                else:
                    res = self._max_min_line(cr, uid, stock_max, line_max_min, context)                        
                    if line_max_min.stock_max > line_max_min.stock_min:
                        orderpoint_obj.create(cr, uid, res)
                    if line_max_min.stock_max < line_max_min.stock_min:
                        raise osv.except_osv(_('Error!'),_('El stock Minimo no puede ser mayor que el stock Maximo, producto "%s"') %(line_max_min.product_id.name))
                             
        return True 

    def action_view_line(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.get_object_reference(cr, uid, 'stock_abastecimiento', 'action_stock_max_min_line_tree')        
        id = result and result[1] or False        
        result = act_obj.read(cr, uid, [id], context=context)[0]
        #compute the number of orders to display
        order_ids = []
        for so in self.browse(cr, uid, ids, context=context):
            order_ids += [order.id for order in so.max_min_line_ids]            
        result['domain'] = "[('id','in',["+','.join(map(str, order_ids))+"])]"
        #_logger.error("COTIZACION 3---: %r", order_ids)
        return result            

class stock_warehouse(osv.osv):
    _inherit ='stock.warehouse'
    _columns = {
        'sequence_abastc_id': fields.many2one('ir.sequence', "Secuencia de abastecimiento", help="Secuencia utilizada para la composicion de productos."), 
    }

class stock_abastecimiento_line(orm.Model):
    _name = 'stock.abastecimiento.line'
    _columns = {
        'product_id': fields.many2one('product.product', 'Producto', required=True, ),
        'product_qty': fields.float('Cantidad solicitada', digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
        'product_qty_abast': fields.float('Cantidad abastecida', digits_compute=dp.get_precision('Product Unit of Measure'),),
        'abastec_id': fields.many2one('stock.abastecimiento', 'Abastecimiento',  ondelete='cascade'),
    }

class stock_abastecimiento(orm.Model):
    _name = 'stock.abastecimiento'

    def _get_total_quantity(self, cr, uid, ids, field, args, context = None):
        res = {}
        i=0        
        for abastecimiento in self.browse(cr, uid, ids, context = context):
            res[abastecimiento.id] = {
                'total_items': 0.0,
                'total_quantity': 0.0,
                'total_quantity_abast': 0.0,
            }
            res[abastecimiento.id]['total_quantity'] = sum([x.product_qty for x in abastecimiento.abastec_line_ids])
            res[abastecimiento.id]['total_quantity_abast'] = sum([x.product_qty_abast for x in abastecimiento.abastec_line_ids])
            for o in abastecimiento.abastec_line_ids:
                i=i+1
            res[abastecimiento.id]['total_items']= i    
            #_logger.error("INNNNNN111111: %r", res[abastecimiento.id]['total_items'])
        return res

    _columns = {
        'name': fields.char('Nombre'),
        'warehouse_id': fields.many2one('stock.warehouse', 'Almacen', required=True, states={'done':[('readonly',True)], 'progress':[('readonly',True)], 'cancel':[('readonly',True)]}),
        'date': fields.datetime('Fecha creacion', required=True, select=1, states={'done':[('readonly',True)],'progress':[('readonly',True)]}),
        'abastec_line_ids': fields.one2many('stock.abastecimiento.line', 'abastec_id', 'Abastecimiento de Productos', states={'done':[('readonly',True)],'progress':[('readonly',True)], 'progress':[('readonly',True)]}),
        'user_id': fields.many2one('res.users', 'Usuario', select=True, track_visibility='onchange'),         
        'state': fields.selection([('draft','Nuevo'),('progress','Pendiente'),('done','Abastecido'),('cancel','Anulado')],string='Estado',readonly=True,required=True),
        'fecha_abast': fields.datetime('Fecha abastecimiento', required=True, select=1, states={'done':[('readonly',True)],'progress':[('readonly',True)], 'progress':[('readonly',True)]}),
        'picking_ids': fields.one2many('stock.picking', 'abastec_picking_id', 'Picking Productos', states={'done':[('readonly',True)],'progress':[('readonly',True)], 'progress':[('readonly',True)]}),
        'total_items': fields.function(_get_total_quantity, type='float', string = 'Total items', multi='all'),
        'total_quantity': fields.function(_get_total_quantity, type='float', string = 'Total productos solicitados', multi='all'),   
        'total_quantity_abast': fields.function(_get_total_quantity, type='float', string = 'Total productos abastecidos', multi='all'),   
    }
    _defaults = {
        'name': lambda obj, cr, uid, context: '/',
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'state': 'draft',
        'user_id': lambda obj, cr, uid, context: uid,        
   }
    _order='fecha_abast desc, name desc'   
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}           
        abastec_id = super(stock_abastecimiento, self).create(cr, uid, vals, context=context)

        warehouse_id = vals.get('warehouse_id', [])
        warehouse_obj =  self.pool.get('stock.warehouse')
        warehouse_campos = warehouse_obj.read(cr, uid, [warehouse_id], ['sequence_abastc_id','lot_stock_id'], context=None)
        sequence_obj = self.pool.get('ir.sequence')

        if warehouse_campos[0]['sequence_abastc_id']:
            vals = {'name': sequence_obj.get_id(cr, uid, warehouse_campos[0]['sequence_abastc_id'][0], context=context)}
            self.write(cr, uid, [abastec_id], vals, context=context)
        else:
            raise osv.except_osv(_('Error!'),_('El almacen no tiene asignado Secuencia de Abastecimiento'))
            
        return abastec_id

    def button_vigente(self, cr, uid, ids, context=None):
        for value in self.browse(cr, uid, ids, context=context):
            if not value.abastec_line_ids:
                raise osv.except_osv(_('Error!'),_('No puede solicitar abastecimiento sin ningun producto, debe presionar el Boton "Calcular abastecimiento" primero!'))
        self.write(cr, uid, ids, { 'state' : 'progress' })
        return True

    def button_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, { 'state' : 'cancel' })
        return True  

    def calcular_abastecimiento (self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        product_obj =  self.pool.get('product.product')
        stock_abastec_obj =  self.pool.get('stock.abastecimiento.line')
        order_max_min_obj =  self.pool.get('stock.warehouse.orderpoint')
        datas = {}           
        for value in self.browse(cr, uid, ids, context=context):
            #se obtiene los ids de todas las reglas de stock en un determinado almacen de todos los productos
            abastec_ids = order_max_min_obj.search(cr, uid, [('warehouse_id','=',value.warehouse_id.id)], context=context)
            for l in abastec_ids: 
                #se coge los campos que nos intersa
                val = order_max_min_obj.read(cr, uid, [l], ['product_id','product_min_qty','product_max_qty'], context=None)
                context = context.copy()
                context.update({'location': value.warehouse_id.lot_stock_id.id })
                prod = self.pool.get('product.product').browse(cr, uid, val[0]['product_id'][0], context=context)
                if val[0]['product_min_qty'] > prod.qty_available:
                    if value.abastec_line_ids:
                        #Consultamos para ver si el producto existe ya en este abastecimiento
                        prod_ids = stock_abastec_obj.search(cr, uid, [('abastec_id','=',value.id),('product_id','=',val[0]['product_id'][0])], context=context)                    
                        if not prod_ids:#Si no existe lo crea
                            stock_abastec_line = {'product_id': prod.id, 'product_qty': val[0]['product_max_qty']- prod.qty_available,'abastec_id':value.id }                     
                            stock_abastec_obj.create(cr,uid,stock_abastec_line,context)
                        else:#si existe lo actualiza
                            stock_abastec_line = {'product_qty': val[0]['product_max_qty']- prod.qty_available,'abastec_id':value.id }
                            stock_abastec_obj.write(cr, uid, prod_ids, stock_abastec_line, context)
                    else:
                        stock_abastec_line = {'product_id': prod.id,'product_qty_abast': 0.0, 'product_qty': val[0]['product_max_qty']- prod.qty_available,'abastec_id':value.id }                     
                        stock_abastec_obj.create(cr,uid,stock_abastec_line,context)                                            
        return True

    def _prepare_order_line_move(self, cr, uid, order, line, picking_id, date_planned, location_id, location_dest_id, qty, context=None):        
        m =  {
            'name': line.product_id.name,
            'picking_id': picking_id,
            'product_id': line.product_id.id,
            'date': date_planned,
            'date_expected': date_planned,
            'product_qty': qty,
            'product_uom': line.product_id.uom_id.id,
            #'partner_id': line.address_allotment_id.id or order.partner_shipping_id.id,
            #'company_id': order.company_id.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id[0],
            'tracking_id': False,
            'state': 'draft',
            'type': 'internal',
            'price_unit': 0.0
        }        
        return m

    def _prepare_picking(self, cr, uid, order, location_id, location_dest_id, context=None):
        return {
            #'name': self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.in'),
            #'name': '/',
            #'origin': order.name + ((order.origin and (':' + order.origin)) or ''),
            'date': datetime.today(),
            'partner_id': 1,
            'invoice_state': 'none',
            'type': 'internal',
            'move_lines' : [],
            'location_id' : location_id,
            'location_dest_id': location_dest_id[0],
            'abastec_picking_id': order.id,
            'stock_journal_id':1,
        }

    def _create_picking(self,cr, uid, order, lines, picking_id=False, context=None):
        if context is None:
            context = {}

        stock_obj =  self.pool.get('stock.picking')
        move_obj =  self.pool.get('stock.move')
        location_obj =  self.pool.get('stock.location')
        abast_line_obj =  self.pool.get('stock.abastecimiento.line')

        i=0.0
        location_id = 12
        location_dest_id = location_obj.search(cr, uid, [('chained_location_id','=',order.warehouse_id.lot_stock_id.id)])
        context.update({'location': location_id })

        for line in lines:
            i=i+1
            if not picking_id:
                picking_id = stock_obj.create(cr, uid, self._prepare_picking(cr, uid, order, location_id, location_dest_id, context), context)   
            qty = None
            product = self.pool.get('product.product').browse(cr, uid, [line.product_id.id], context)[0]
            if product.procedencia == 'import':
                if product.qty_disponible >= line.product_qty :
                    qty =  line.product_qty
                else:
                    qty = product.qty_disponible                
            else:
                if product.qty_available >= line.product_qty :
                    qty =  line.product_qty
                else:
                    qty = product.qty_available
            if qty >0:
                move_id = move_obj.create(cr, uid, self._prepare_order_line_move(cr, uid, order, line, picking_id, order.fecha_abast, location_id, location_dest_id, qty,context=context))                
                #cr.execute("UPDATE stock_abastecimiento_line SET product_qty_abast=%s WHERE id=%s", (qty, line.id))
                abast_line_obj.write(cr, uid, line.id, {'product_qty_abast': qty}, context)
            if i>10:
                i=0
                picking_id=False
            #_logger.error("MINIMO2: %r", pikcing_id) 
        return True

    def generar_guia(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            self._create_picking(cr, uid, order, order.abastec_line_ids, None, context=context)
            self.write(cr, uid, order.id, {'state': 'done'}, context)            
        return True
    
class stock_picking(orm.Model):
    _inherit='stock.picking'
    _columns= {
        'abastec_picking_id': fields.many2one('stock.abastecimiento', 'Abastecimiento Stock', ondelete='cascade'),
    }