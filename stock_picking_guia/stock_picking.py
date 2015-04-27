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


class stock_journal(osv.osv):
    _name = "stock.journal"
    _inherit = 'stock.journal'
    _columns = {
            'sequence_id': fields.many2one('ir.sequence','Secuencia'),
            'warehouse_id': fields.many2one('stock.warehouse','Almacen'),
            #'carrier_id':fields.many2one("delivery.carrier","Carrier"),
	        'company_id': fields.many2one('res.company', 'Company', required=True, select=1, help="Company related to this journal"),
            'user_ids': fields.many2many('res.users','stock_journal_users','journal_id','user_id',string='Permisos de usuarios',help="User Access use empty for full access"),
            'group_ids': fields.many2many('res.groups', 'stock_journal_rel', 'sequence_id', 'groups_id', 'Groups'),
        }
    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }
stock_journal()



class stock_picking(osv.osv):
    _name = "stock.picking"
    _inherit = 'stock.picking'

    _columns = {     

    } 

    def action_done(self, cr, uid, ids, context=None):
        """Changes picking state to done.
        
        This method is called at the end of the workflow by the activity "done".
        @return: True
        """
        for picking in self.browse(cr, uid, ids, context=context):
            res = {}
            #if picking.name or picking.name == '/':
            if picking.name[:2] != 'GR': #CUANDO SE ANULA LA GUIA Y SE VUELVE A BORRADOR NO ASIGNE NUEVA GUIA
                if picking.type == 'out':
                    if picking.stock_journal_id and picking.stock_journal_id.sequence_id:
                        res['name'] = self.pool.get('ir.sequence').get_id(cr, uid, picking.stock_journal_id.sequence_id.id)
                if picking.type == 'internal'and picking.name[:3] != 'INT':#INT para evitar que al producir coga un numero de guia
                    if picking.stock_journal_id and picking.stock_journal_id.sequence_id:
                        res['name'] = self.pool.get('ir.sequence').get_id(cr, uid, picking.stock_journal_id.sequence_id.id)
            #_logger.error("NAMEEEEEEEEEEE----: %r", picking.name[:2])           
            if res:
                self.write(cr,uid,[picking.id],res,context=context)        
        self.write(cr, uid, ids, {'state': 'done', 'date_done': time.strftime('%Y-%m-%d %H:%M:%S')})
        return True


    def draft_force_assign(self, cr, uid, ids , context=None, *args):
        """ Confirms picking directly from draft state.
        @return: True
        """
        pickings = self.browse(cr, uid, ids, context=context)
        for picking in pickings:  
            res={}
            if picking.type not in ('in','out'): #ASIGNACION DE GUIA
                if picking.name[:2] != 'GR':
                    if picking.type == 'out':
                        if picking.stock_journal_id and picking.stock_journal_id.sequence_id:
                            res['name'] = self.pool.get('ir.sequence').get_id(cr, uid, picking.stock_journal_id.sequence_id.id)
                    if picking.type == 'internal' and picking.name[:3] != 'INT':
                        if picking.stock_journal_id and picking.stock_journal_id.sequence_id:
                            res['name'] = self.pool.get('ir.sequence').get_id(cr, uid, picking.stock_journal_id.sequence_id.id)
                if res:
                    self.write(cr,uid,[picking.id],res,context=context) 

        wf_service = netsvc.LocalService("workflow")
        for pick in self.browse(cr, uid, ids):
            if not pick.move_lines:
                raise osv.except_osv(_('Error!'),_('You cannot process picking without stock moves.'))
            wf_service.trg_validate(uid, 'stock.picking', pick.id,
                'button_confirm', cr)
        return True

    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirms picking.
        @return: True
        """
        pickings = self.browse(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'state': 'confirmed'})
        todo = []
        for picking in pickings:
            for r in picking.move_lines:
                #COMPRUEBA LAS CANTIDADES ANTES DE CONFIRMAR UN TRASLADO INTERNO FECHA CAMBIO 25/10/2014
                if picking.type == 'internal' and r.location_id.usage == 'internal' :
                    if context is None:
                            context = {}                    
                    c = context.copy()
                    c.update({'location': r.location_id.id })
                    product = self.pool.get('product.product').browse(cr, uid, [r.product_id.id], c)[0]
                    #_logger.error("ubicATION----: %r", r.location_id.name)
                    #_logger.error("CONDFIRR----: %r", product.qty_available)
                    #if product.qty_available < r.product_qty and  (product.type=='product') :
                    #    raise osv.except_osv(_('Warning!'),_('Verifique su stock, no hay stock suficiente, Producto: "%s"') %(product.name))
                    #FIN COMPRUEBA LAS CANTIDADES ANTES DE CONFIRMAR

                if r.state == 'draft':
                    todo.append(r.id)
        todo = self.action_explode(cr, uid, todo, context)
        if len(todo):
            #AGREGANDO PARA QUE SE PUEDA EJECUTAR EN ENVIO INTERCOMPANY
            for picking in pickings: 
                for r in picking.move_lines:
                    if r.location_dest_id.usage == 'transit':
                        uid=1
            #FIN
            self.pool.get('stock.move').action_confirm(cr, uid, todo, context=context)
        return True

    def action_move(self, cr, uid, ids, context=None):
        """Process the Stock Moves of the Picking
        
        This method is called by the workflow by the activity "move".
        Normally that happens when the signal button_done is received (button 
        "Done" pressed on a Picking view). 
        @return: True
        """
        for pick in self.browse(cr, uid, ids, context=context):
            todo = []
            for move in pick.move_lines:
                if move.state == 'draft':
                    self.pool.get('stock.move').action_confirm(cr, uid, [move.id],
                        context=context)
                    todo.append(move.id)
                elif move.state in ('assigned','confirmed'):
                    todo.append(move.id)
            if len(todo):
                #AGREGADO PARA TRASLADOS INTERCOMPANY
                for picking in self.browse(cr, uid, ids, context=context): 
                    for r in picking.move_lines:
                        if r.location_dest_id.usage == 'transit':
                            uid=1
                #FIN
                self.pool.get('stock.move').action_done(cr, uid, todo, context=context)
        return True

stock_picking()

