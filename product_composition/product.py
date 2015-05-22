
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


class stock_location(osv.osv):
    _name = 'stock.location'
    _inherit ='stock.location'
    _columns = {
        'usage': fields.selection([('supplier', 'Supplier Location'), ('view', 'View'), ('internal', 'Internal Location'), ('customer', 'Customer Location'), ('inventory', 'Inventory'), ('procurement', 'Procurement'), ('production', 'Production'), ('transit', 'Transit Location for Inter-Companies Transfers'),('composition', 'Composicion')], 'Location Type', required=True,
                 help="""* Supplier Location: Virtual location representing the source location for products coming from your suppliers
                       \n* View: Virtual location used to create a hierarchical structures for your warehouse, aggregating its child locations ; can't directly contain products
                       \n* Internal Location: Physical locations inside your own warehouses,
                       \n* Customer Location: Virtual location representing the destination location for products sent to your customers
                       \n* Inventory: Virtual location serving as counterpart for inventory operations used to correct stock levels (Physical inventories)
                       \n* Procurement: Virtual location serving as temporary counterpart for procurement operations when the source (supplier or production) is not known yet. This location should be empty when the procurement scheduler has finished running.
                       \n* Production: Virtual counterpart location for production operations: this location consumes the raw material and produces finished products
                       \n* Composition: Virtual counterpart location for composition operations: Ubicacion virtual de contrapartida para operaciones de composicion
                      """, select = True),
        'sequence_composition_id': fields.many2one('ir.sequence', "Secuencia de Composicion", help="Secuencia utilizada para la composicion de productos."), 
    }

class product_composition_line(orm.Model):
    _name = 'product.composition.line'
    _rec_name = 'composition_id'
    _columns = {
        'composition_id': fields.many2one( 'product.composition', 'Product Composition', ondelete='cascade'),
        'product_id': fields.many2one('product.product', 'Producto', required=True),
        'quantity': fields.float('Cantidad', required=True),       
    }


class product_composition(orm.Model):
    _name = 'product.composition'
    _columns = {
        'name': fields.char('Nombre'),
        'product_id': fields.many2one('product.product', 'Producto', required=True),
        'quantity': fields.float('Cantidad', required=True),
        'composition_line_ids': fields.one2many('product.composition.line', 'composition_id', 'Products Composition', help='List of products that are part of this composition.' ),
        'active': fields.boolean('Activo'),
    }

    _defaults = {
        'quantity': lambda *a: 1.0,
        'active': lambda *a: 1,
   }

    def onchange_product_id(self, cr, uid, ids, product_id, name, context=None):
        """ Changes UoM and name if product_id changes.
        @param name: Name of the field
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        if product_id:
            prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            return {'value': {'name': prod.name, 'product_uom': prod.uom_id.id}}
        return {}

class stock_move(orm.Model):
    _inherit = 'stock.move'
    _columns = {
        'make_move_id': fields.many2one('product.make', 'Production Composition',  ondelete='cascade'),
    }

class product_make_line(orm.Model):
    _name = 'product.make.line'
    _columns = {
        'product_id': fields.many2one('product.product', 'Producto', required=True, ),
        'product_qty': fields.float('Cantidad', digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
        'make_id': fields.many2one('product.make', 'Production Composition',  ondelete='cascade'),
        'concepto': fields.selection([('consumir', 'Consumir'),('producir', 'Producir')],'Consume / Produce', select = True, readonly=False,),
    }

class product_make(osv.osv):
    _name = 'product.make'
    _columns = {
        'name': fields.char('Nombre',),
        'location_id': fields.many2one('stock.location', 'Ubicacion origen', required=True,states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
        'location_dest_id': fields.many2one('stock.location', 'Ubicacion destino', required=True,states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
        'composition_id': fields.many2one('product.composition', 'Producto', required=True,states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
        'quantity': fields.float('Cantidad', required=True, states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
        'date': fields.datetime('Fecha', required=True, select=1, states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
        'concepto': fields.selection([('componer', 'Composicion de productos'),('descomponer', 'Descomposicion de productos')],'Tipo de operacion', select = True, required=True, states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
        'move_lines_ids': fields.one2many('stock.move', 'make_move_id', 'Productos consumidos', states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
        'make_line_ids': fields.one2many('product.make.line', 'make_id', 'Productos planificados', states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
        'state': fields.selection([('draft','Nuevo'),('done','Realizado'),('cancel','Cancelado')],string='Estado',readonly=True,required=True),
    }
    _order='date desc'

    def _default_location_source(self, cr, uid, context=None):
        """ Gets default location for source location
        @return: locaion id or False
        """
        mod_obj = self.pool.get('ir.model.data')
        picking_type = context.get('picking_type')
        location_id = False
       
        location_xml_id = 'location_composicion'
        if location_xml_id:
            try:
                location_model, location_id = mod_obj.get_object_reference(cr, uid, 'product_composition', location_xml_id)
                with tools.mute_logger('openerp.osv.orm'):
                    self.pool.get('stock.location').check_access_rule(cr, uid, [location_id], 'read', context=context)
            except (orm.except_orm, ValueError):
                location_id = False

        return location_id

    _defaults = {
        'quantity': lambda *a: 1.0,
        'name': lambda obj, cr, uid, context: '/',
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'state': 'draft',
        'location_id': _default_location_source,
   }

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}

        product_make_id = super(product_make, self).create(cr, uid, vals, context=context)

        location_id = vals.get('location_dest_id', [])
        location = self.pool.get('stock.location').browse(cr, uid, location_id, context)
        sequence_obj = self.pool.get('ir.sequence')

        #Permite enviar el id del almacen de despacho
        context = context.copy()
        if location_id:
            context.update({'location': location_id })
        #Fin            

        ##SECUENCIAS POR UBICACION
        if location and location.sequence_composition_id:
            vals = {'name': sequence_obj.get_id(cr, uid, location.sequence_composition_id.id, context=context)}
            self.write(cr, uid, [product_make_id], vals, context=context)
        else:
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'product.make')
            self.write(cr, uid, [product_make_id], vals, context=context)
        #FIN SECUENCIAS


        for compos_order in self.browse(cr, uid, [product_make_id], context=context):
            composit = self.pool.get('product.composition').browse(cr, uid, compos_order.composition_id.id, context=context)
            make_line_obj = self.pool.get('product.make.line')
            if compos_order.concepto == 'componer':      
                make_line_ferts = {
                    'product_id' : composit.product_id.id,
                    'product_qty' : composit.quantity*compos_order.quantity,
                    'concepto': 'producir',
                    'make_id': product_make_id,
                    }
                make_line_obj.create(cr, uid, make_line_ferts)
                for m in composit.composition_line_ids:
                    prod = self.pool.get('product.product').browse(cr, uid, m.product_id.id, context=context)
                    if prod.qty_available < m.quantity*compos_order.quantity:
                        raise osv.except_osv(_('Warning!'),_('Esta intentando consumir un producto en una cantidad mayor a la cant. real, Producto: "%s" (Cant. real:%d).') %(prod.name, prod.qty_available,))
                    else:
                        concepto='consumir'
                        self._partial_make_for(cr, uid, m, product_make_id,compos_order.quantity, concepto)
            else:
                prod = self.pool.get('product.product').browse(cr, uid, composit.product_id.id, context=context)
                if prod.qty_available < composit.quantity*compos_order.quantity:
                        raise osv.except_osv(_('Warning!'),_('Esta intentando consumir un producto en una cantidad mayor a la cant. real, Producto: "%s" (Cant. real:%d).') %(prod.name, prod.qty_available,))
                else:                        
                    make_line_ferts = {
                        'product_id' : composit.product_id.id,
                        'product_qty' : composit.quantity*compos_order.quantity,
                        'concepto': 'consumir',
                        'make_id': product_make_id,
                        }
                    make_line_obj.create(cr, uid, make_line_ferts)
                    for m in composit.composition_line_ids:
                        concepto='producir'
                        self._partial_make_for(cr, uid, m, product_make_id,compos_order.quantity, concepto)
        return product_make_id

    def _partial_make_for(self, cr, uid, make, product_make_id, quantity, concepto):

        make_line = {
            'product_id' : make.product_id.id,
            'product_qty' : make.quantity*quantity,
            'concepto': concepto,
            'make_id': product_make_id,
        }
        make_line_obj = self.pool.get('product.make.line')
        make_line_create_id = make_line_obj.create(cr, uid, make_line, context=None)
        return make_line

    def _move_composition_line(self, cr, uid, composition, m, context=None):
        stock_move = self.pool.get('stock.move')
        move_id=None
        if m.concepto == 'producir':
            source_location_id = composition.location_id.id
            destination_location_id = composition.location_dest_id.id
            data = {
            'name': composition.name,
            'date': composition.date,
            'date_expected': composition.date,
            'product_id': m.product_id.id,
            'product_uom': m.product_id.uom_id.id,
            'product_qty': m.product_qty,
            'location_id': source_location_id,
            'location_dest_id': destination_location_id,
            'state': 'draft',
            'make_move_id': composition.id,
            }
            move_id = stock_move.create(cr, uid, data, context=context)
            stock_move.action_done(cr, uid, [move_id], context)

        if m.concepto == 'consumir':
            destination_location_id = composition.location_id.id
            source_location_id = composition.location_dest_id.id
            data = {
            'name': composition.name,
            'date': composition.date,
            'date_expected': composition.date,
            'product_id': m.product_id.id,
            'product_uom': m.product_id.uom_id.id,
            'product_qty': m.product_qty,
            'location_id': source_location_id,
            'location_dest_id': destination_location_id,
            'state': 'draft',
            'make_move_id': composition.id,
            }
            move_id = stock_move.create(cr, uid, data, context=context)
            stock_move.action_done(cr, uid, [move_id], context)
        return move_id

    def button_componer(self, cr, uid, ids, context=None):
        for composition in self.browse(cr, uid, ids, context=context):
            for m in composition.make_line_ids:
                self._move_composition_line(cr, uid, composition, m, context=context)
        self.write(cr, uid, ids, { 'state' : 'done' })
        return True

    def button_cancel(self, cr, uid, ids, context=None):
        """ Cancels the production order and related stock moves.
        @return: True
        """
        if context is None:
            context = {}
        move_obj = self.pool.get('stock.move')
        for make in self.browse(cr, uid, ids, context=context):
            if make.state == 'done': #and make.picking_id.state not in ('draft', 'cancel'):
                raise osv.except_osv(
                    _('No se puede cancelar esta operacion!'),
                    _('Primero deberias cancelar los movimientos relacionados a esta composicion.'))
            if make.move_lines_ids:
                move_obj.action_cancel(cr, uid, [x.id for x in make.move_lines_ids])
            move_obj.action_cancel(cr, uid, [x.id for x in make.move_lines_ids])
        self.write(cr, uid, ids, {'state': 'cancel'})
        return True

    def unlink(self, cr, uid, ids, context=None):
        states = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for s in states:
            if s['state'] in ['draft', 'cancel']:
                unlink_ids.append(s['id'])
            else:
                raise osv.except_osv(_('Invalid Action!'), _('No se puede eliminar esta composicion, para hacerlo primero debe cancelar esta operacion'))
        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)



