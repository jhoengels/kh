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


class stock_location(osv.osv):
    _inherit ='stock.location'
    def __init__(self, *args):        
        super(stock_location, self).__init__(*args)
        option = ('ajuste', 'Ajuste Inventario')
        type_selection = self._columns['usage'].selection
        if option not in type_selection:
            type_selection.append(option)


class stock_move(orm.Model):
    _inherit = 'stock.move'
    _columns = {
        'ajuste_move_id': fields.many2one('stock.ajuste', 'Ajuste relacionado',  ondelete='cascade'),
    }

class stock_ajuste_line(orm.Model):
    _name = 'stock.ajuste.line'
    _columns = {
        'product_id': fields.many2one('product.product', 'Producto', required=True, ),
        'product_qty': fields.float('Cantidad', digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
        'ajuste_id': fields.many2one('stock.ajuste', 'Ajuste',  ondelete='cascade'),
    }

class stock_ajuste(osv.osv):
    _name = 'stock.ajuste'
    _columns = {
        'name': fields.char('Nombre',),
        'descripcion': fields.char('Descripcion',),
        'user_id': fields.many2one('res.users', 'Usuario', select=True, track_visibility='onchange'),        
        'location_id': fields.many2one('stock.location', 'Ubicacion origen', required=True,states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
        'location_dest_id': fields.many2one('stock.location', 'Ubicacion destino', required=True,states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
        'date': fields.datetime('Fecha', required=True, select=1, states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
        'concepto': fields.selection([('ingreso', 'Ingreso por ajuste de inventario'),('salida', 'Salida por ajuste de inventario')],'Concepto', select = True, required=True, states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
        'move_lines_ids': fields.one2many('stock.move', 'ajuste_move_id', 'Moviminetos relacionado', states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
        'ajuste_line_ids': fields.one2many('stock.ajuste.line', 'ajuste_id', 'Productos para ajustes', states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
        'state': fields.selection([('draft','Nuevo'),('done','Realizado'),('cancel','Cancelado')],string='Estado',readonly=True,required=True),
    }
    _order='date desc'

    def _default_location_source(self, cr, uid, context=None):
        """ Gets default location for source location
        @return: locaion id or False
        """
        mod_obj = self.pool.get('ir.model.data')
        location_id = False    
        location_xml_id = 'location_ajuste_inventario'
        if location_xml_id:
            try:
                location_model, location_id = mod_obj.get_object_reference(cr, uid, 'stock_ajuste', location_xml_id)
                with tools.mute_logger('openerp.osv.orm'):
                    self.pool.get('stock.location').check_access_rule(cr, uid, [location_id], 'read', context=context)
            except (orm.except_orm, ValueError):
                location_id = False

        return location_id

    _defaults = {
        'name': lambda obj, cr, uid, context: '/',
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'state': 'draft',
        'location_id': _default_location_source,
        'user_id': lambda obj, cr, uid, context: uid,        
   }

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if vals.get('name','/')=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'ajuste.inventario')
        ajuste_id = super(stock_ajuste, self).create(cr, uid, vals, context=context)
        return ajuste_id

    def _move_ajuste_line(self, cr, uid, ajuste, m, context=None):
        stock_move = self.pool.get('stock.move')
        move_id=None
        if ajuste.concepto == 'ingreso':
            source_location_id = ajuste.location_id.id
            destination_location_id = ajuste.location_dest_id.id
            data = {
            'name': ajuste.name,
            'date': ajuste.date,
            'date_expected': ajuste.date,
            'product_id': m.product_id.id,
            'product_uom': m.product_id.uom_id.id,
            'product_qty': m.product_qty,
            'location_id': source_location_id,
            'location_dest_id': destination_location_id,
            'state': 'draft',
            'ajuste_move_id': ajuste.id,
            }
            move_id = stock_move.create(cr, uid, data, context=context)
            stock_move.action_done(cr, uid, [move_id], context)

        if ajuste.concepto == 'salida':
            destination_location_id = ajuste.location_id.id
            source_location_id = ajuste.location_dest_id.id
            data = {
            'name': ajuste.name,
            'date': ajuste.date,
            'date_expected': ajuste.date,
            'product_id': m.product_id.id,
            'product_uom': m.product_id.uom_id.id,
            'product_qty': m.product_qty,
            'location_id': source_location_id,
            'location_dest_id': destination_location_id,
            'state': 'draft',
            'ajuste_move_id': ajuste.id,
            }
            move_id = stock_move.create(cr, uid, data, context=context)
            stock_move.action_done(cr, uid, [move_id], context)
        return move_id

    def button_validar(self, cr, uid, ids, context=None):
        for ajuste in self.browse(cr, uid, ids, context=context):
            for m in ajuste.ajuste_line_ids:
                self._move_ajuste_line(cr, uid, ajuste, m, context=context)
        self.write(cr, uid, ids, { 'state' : 'done' })
        return True

    def button_cancel(self, cr, uid, ids, context=None):
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



