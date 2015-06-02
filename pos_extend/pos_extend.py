
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
import openerp.addons.decimal_precision as dp

from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)


class stock_location(osv.osv):
    _name = 'stock.location'
    _inherit ='stock.location'
    _columns = {
        'bajo_pedido': fields.boolean('Despachos bajo pedidos de tienda',help="Para cuando las tiendas haga la venta desde Terminal de Punto de Venta y los productos salgan de un este Almacen "), 
    }

class sale_shop(osv.osv):
    _inherit = "sale.shop"
    _columns = {
        'sequencepos_id': fields.many2one('ir.sequence', "Secuencia orden venta TPV", help="La secuencia utilizada para las ordenes de venta de un TPV"),       
    }


class pos_session(osv.osv):
    _inherit = 'pos.session'

    def _confirm_orders(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")

        for session in self.browse(cr, uid, ids, context=context):
            local_context = dict(context or {}, force_company=session.config_id.journal_id.company_id.id)
            order_ids = [order.id for order in session.order_ids if order.state == 'paid']

            move_id = self.pool.get('account.move').create(cr, uid, {'ref' : session.name, 'journal_id' : session.config_id.journal_id.id, }, context=local_context)

            self.pool.get('pos.order')._create_account_move_line(cr, uid, order_ids, session, move_id, context=local_context)

            for order in session.order_ids:
                if order.state not in ('paid', 'invoiced','cancel'):
                    raise osv.except_osv(
                        _('Error!'),
                        _("You cannot confirm all orders of this session, because they have not the 'paid' status"))
                else:
                    wf_service.trg_validate(uid, 'pos.order', order.id, 'done', cr)

        return True

    def open_frontend_cb(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        if not ids:
            return {}
        for session in self.browse(cr, uid, ids, context=context):
            if session.user_id.id != uid:
                raise osv.except_osv(
                        _('Error!'),
                        _("You cannot use the session of another users. This session is owned by %s. Please first close this one to use this point of sale." % session.user_id.name))
        context.update({'active_id': ids[0]})
        
        #REESCRITO PARA QUE QUE AL HACER CLIC EN "CONTINUAR VENTA" NO HABRA LA VENTANA TOUCH
        return {
            'name': _('Pos order'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'pos.order',
            #'res_id': session_id,
            'view_id': False,
            'type': 'ir.actions.act_window',
        }


class pos_order(osv.osv):
    _name = 'pos.order'
    _inherit ='pos.order'



    def _amount_subtotal(self, cr, uid, ids, name, args, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            val1 = val2 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.lines:
                #_logger.error("SHOP ID 0: %r", line.price_subtotal)
                val1 += line.price_subtotal_incl
                val2 += line.price_subtotal
            res[order.id] = cur_obj.round(cr, uid, cur, val2)
            
        return res    

    _columns = {
        'es_factura': fields.boolean('Facturada', states={'draft': [('readonly', False)],} ),
        'almacendespacho_id' : fields.many2one('stock.location', 'Almacen depacho', help="Ubicacion desde donde se despachara el producto al cliente, dejar en blanco si sale de la misma tienda", states={'draft': [('readonly', False)],} ),
        'doc_number': fields.char('RUC/DNI',size=32, states={'draft': [('readonly', False)],} ),
        #'devolucion': fields.char('Devolucion de',size=64, states={'draft': [('readonly', False)],} ),
        'fecha_expected': fields.datetime('Fecha entrega al cliente', required=False, readonly=False, select=True, states={'draft': [('readonly', False)]}),
        'partner_shipping_id': fields.many2one('res.partner', 'Direccion de entrega', states={'draft': [('readonly', False)],} ),

        'amount_subtotal': fields.function(_amount_subtotal, digits_compute=dp.get_precision('Point Of Sale'), string='Sub Total',method=True, type='float',store=True),
    }

    _defaults = {
        'es_factura': False,
    }

    def write(self, cr, uid, ids, vals, context=None):
        res = super(pos_order, self).write(cr, uid, ids, vals, context=context)
        #If you change the partner of the PoS order, change also the partner of the associated bank statement lines
        partner_obj = self.pool.get('res.partner')
        bsl_obj = self.pool.get("account.bank.statement.line")
        if 'partner_id' in vals:
            for posorder in self.browse(cr, uid, ids, context=context):
                if posorder.invoice_id:
                    raise osv.except_osv( _('Error!'), _("You cannot change the partner of a POS order for which an invoice has already been issued."))
                if vals['partner_id']:
                    p_id = partner_obj.browse(cr, uid, vals['partner_id'], context=context)
                    part_id = partner_obj._find_accounting_partner(p_id).id
                else:
                    part_id = False
                bsl_ids = [x.id for x in posorder.statement_ids]
                bsl_obj.write(cr, uid, bsl_ids, {'partner_id': part_id}, context=context)

        #Permite enviar el id del almacen de despacho o de tienda al contexto
        
        if context is None:
            context = {}
        
        c = context.copy()
        for posorder in self.browse(cr, uid, ids, context=context):
            if posorder.almacendespacho_id:
                c.update({'location': posorder.almacendespacho_id.id })
            else:
                c.update({'location': posorder.shop_id.warehouse_id.lot_stock_id.id })
                
        #Fin        
        for order in self.browse(cr, uid, ids, context=c):
            for line in order.lines:
                if order.state == 'draft':
                    if order.almacendespacho_id:
                        continue
                        #if line.product_id.procedencia == 'import' :
                        #if line.product_id.qty_disponible < line.qty:
                        #    raise osv.except_osv(_('Warning!'),_('No puede vender un producto importado de almacen PRINCIPAL con stock insuficiente, Producto: "%s" (Cant. Dispo:%d).') %(line.product_id.name, line.product_id.qty_disponible,))
                    else:
                        if not order.picking_id:  
                            if line.product_id.qty_disponible < line.qty:
                                raise osv.except_osv(_('Warning!'),_('No puede vender un producto con stock insuficiente, Producto: "%s" (Cant. Dispo:%d).') %(line.product_id.name, line.product_id.qty_disponible,))
        #Fin     
        return res

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(pos_order, self).default_get(cr, uid, fields, context=context)
        order_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        so = self.pool.get('pos.session')
        session_ids = so.search(cr, uid, [('state','=', 'opened')], context=context)

        uo = self.pool.get('res.users')
        user_id = uo.search(cr, uid, [('id','=', uid)], context=context)

        for session in so.browse(cr, uid, session_ids, context=context):
            for user in uo.browse(cr, uid, user_id, context=context):
                if session.config_id.shop_id.id == user.shop_id.id:
                    res.update(session_id=session.id )
        return res   

    def onchange_partner_id(self, cr, uid, ids, part=False, context=None):
        if not part:
            return {'value': {'doc_number':False,'es_factura': False}}
        #part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        part_id = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        addr = self.pool.get('res.partner').address_get(cr, uid, [part_id.id], ['delivery', 'invoice', 'contact'])

        pricelist = self.pool.get('res.partner').browse(cr, uid, part, context=context).property_product_pricelist.id
        doc_number = self.pool.get('res.partner').browse(cr, uid, part, context=context).doc_number
        if doc_number:
            doc = doc_number.strip()
            if len(doc) == 11:
                return {'value': {'pricelist_id': pricelist, 'partner_shipping_id': addr['delivery'], 'doc_number':doc_number, 'es_factura': True}}
        
        return {'value': {'pricelist_id': pricelist, 'partner_shipping_id': addr['delivery'], 'doc_number':doc_number,'es_factura': False}}
    
    def onchange_ruc_dni(self, cr, uid, ids, ruc_dni, context=None):
        if context is None:
            context = {}
        value = {}
      
        partner_obj = self.pool.get('res.partner')
        if ruc_dni:
            partner_id = partner_obj.search(cr,uid,[('doc_number','=',ruc_dni)])
            if partner_id:
                value.update({
                       'partner_id': partner_id,
                    })
                return {'value': value}
            else:
                raise osv.except_osv(_('Warning!'), _('Usuario no registrado en el sistema.'))
        else:
            return {'value': {'pricelist_id': False, 'partner_id':False,'es_factura': False}}

    def create(self, cr, uid, values, context=None):

        #values['name'] = self.pool.get('ir.sequence').get(cr, uid, 'pos.order')

        pos_order_id = super(pos_order, self).create(cr, uid, values, context=context)
        #_logger.error("pos order ID 1: %r", pos_order_id)

        for order in self.browse(cr, uid, [pos_order_id], context=context):
            shop_id = order.shop_id
        #_logger.error("SHOP ID 0: %r", shop_id.id)
        shop = self.pool.get('sale.shop').browse(cr, uid, shop_id.id, context)
        sequence_obj = self.pool.get('ir.sequence')

        if shop and shop.sequencepos_id:
            values = {'name': sequence_obj.get_id(cr, uid, shop.sequencepos_id.id, context=context)}      
            self.write(cr, uid, [pos_order_id], values, context=context)

        if context is None:
            context = {}

        #Permite enviar el id del almacen de despacho al contexto
        c = context.copy()
        for posorder in self.browse(cr, uid, [pos_order_id], context=context):
            if posorder.almacendespacho_id:
                c.update({'location': posorder.almacendespacho_id.id })
            else:
                c.update({'location': posorder.shop_id.warehouse_id.lot_stock_id.id })
        #Fin

        for order in self.pool.get('pos.order').browse(cr, uid, [pos_order_id], context=c):
            for line in order.lines:
                if  line.product_id.procedencia == 'import' and order.almacendespacho_id:
                    if line.product_id.qty_disponible < line.qty:
                        raise osv.except_osv(_('Warning!'),_('No puede vender un producto importado de almacen PRINCIPAL con stock insuficiente, Producto: "%s" (Cant. Dispo:%d).') %(line.product_id.name, line.product_id.qty_disponible,))
                if not order.almacendespacho_id:
                    if line.product_id.qty_disponible < line.qty:
                        raise osv.except_osv(_('Warning!'),_('No puede vender un producto con stock insuficiente, Producto: "%s" (Cant. Dispo:%d).') %(line.product_id.name, line.product_id.qty_disponible,))
        #fin
        return pos_order_id

    def create_picking(self, cr, uid, ids, context=None):
        """Create a picking for each order and validate it."""
        picking_obj = self.pool.get('stock.picking.out')
        partner_obj = self.pool.get('res.partner')
        move_obj = self.pool.get('stock.move')

        for order in self.browse(cr, uid, ids, context=context):
            addr = order.partner_id and partner_obj.address_get(cr, uid, [order.partner_id.id], ['delivery']) or {}
            if order.almacendespacho_id: #PARA SACAR EL PEDIDO DEL ALMACEN PRINCIPAL
                if order.partner_id:
                    destination_id = order.partner_id.property_stock_customer.id 
                else:
                    destination_id = partner_obj.default_get(cr, uid, ['property_stock_customer'], context=context)['property_stock_customer']
                uid=1 
                picking_id = picking_obj.create(cr, uid, {
                    'origin': order.name,
                    #'partner_id': addr.get('delivery',False) ,
                    'partner_id': order.partner_shipping_id.id,
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
                        'date_expected': order.fecha_expected,#PARA ESPECIFICAR UNA FEHCA DE ENTREGA EN EL ALMACEN
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
                    #'partner_id': addr.get('delivery',False),
                    'partner_id': order.partner_shipping_id.id,#OBTIENDO DATOS DEL CAMPO DIRECCION DE ENVIO EN LA ORDEN
                    'type': 'in' if order.devolucion else 'out', 
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

    def pos_print_report(self, cr, uid, ids, context=None):
        '''
        This function prints the invoice and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        self.write(cr, uid, ids, {'sent': True}, context=context)
        datas = {
             'ids': ids,
             'model': 'pos.order',
             'form': self.read(cr, uid, ids[0], context=context)
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'pos.order.print.ticket',
            'datas': datas,
            'nodestroy' : True
        }

    #ANULA LOS PAGOS SI UNA SESION NO HA SIDO CERRADA AUN.
    def cancel_payment(self, cr, uid, ids, context=None):
        line_pool = self.pool.get('account.bank.statement.line')
        for order in self.browse(cr, uid, ids, context=context):
            if order.session_id.state != "closed":        
                line_ids = [line.id for line in order.statement_ids]
                line_pool.unlink(cr, uid, line_ids, context=context)
                #_logger.error("SHOP ID 0: %r", order.name)
            else:
                raise osv.except_osv(_('Error!'), _('No se puede eliminar los pagos de una orden de venta cuya caja a sido cerrado.'))
        self.write(cr, uid, ids, {'state': 'draft'}, context=context)        
        return True
    #PARA QUE DESPUES DE HACER UN PAGO DE CAMBIE DE ESTADO    
    def action_paid2(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'paid'}, context=context)
        return True

    #ANULA UN TICKET
    def cancel_order(self, cr, uid, ids, context=None):
        """ Changes order state to cancel
        @return: True
        """
        stock_picking_obj = self.pool.get('stock.picking')
        wf_service = netsvc.LocalService("workflow")
        for order in self.browse(cr, uid, ids, context=context):
            #inicio
            if order.session_id.state == "closed":
                raise osv.except_osv(_('Error!'), _('No se puede eliminar un ticket de una caja cerrada , debe de generar una note de credito'))
            if order.session_id.state != "closed":
                if order.statement_ids:
                    raise osv.except_osv(_('ANULAR PAGO!'), _('No se puede eliminar un ticket PAGADO, Debe de anular el pago pirmero!'))
                #self.cancel_payment(cr, uid, ids, context=context)                
                if order.picking_id:
                    if order.almacendespacho_id:
                        uid=1
                    wf_service.trg_validate(uid, 'stock.picking', order.picking_id.id, 'button_cancel', cr)
            #fin
            if order.picking_id:
                if stock_picking_obj.browse(cr, uid, order.picking_id.id, context=context).state <> 'cancel':
                    raise osv.except_osv(_('Error!'), _('Unable to cancel the picking.'))

        self.write(cr, uid, ids, {'state': 'cancel', 'amount_total': 0.0}, context=context)
        return True

pos_order()

class pos_order_line(osv.osv):
    _inherit = 'pos.order.line'  

    def _amount_line_all(self, cr, uid, ids, field_names, arg, context=None):
        res = dict([(i, {}) for i in ids])
        account_tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids, context=context):
            taxes_ids = [ tax for tax in line.product_id.taxes_id if tax.company_id.id == line.order_id.company_id.id ]
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = account_tax_obj.compute_all(cr, uid, taxes_ids, price, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)

            cur = line.order_id.pricelist_id.currency_id
            res[line.id]['price_subtotal'] = cur_obj.round(cr, uid, cur, taxes['total'])
            res[line.id]['price_subtotal_incl'] = cur_obj.round(cr, uid, cur, taxes['total_included'])
            #_logger.error("SHOP ID 1: %r", res)
        return res
    _columns = {#Añadimos precision para poder generar los asientos correctamente
        'price_subtotal': fields.function(_amount_line_all, multi='pos_order_line_amount', string='Subtotal w/o Tax',digits_compute=dp.get_precision('Point Of Sale'), ),
        'price_subtotal_incl': fields.function(_amount_line_all, multi='pos_order_line_amount', string='Subtotal',digits_compute=dp.get_precision('Point Of Sale'), ),
  
    }
    def onchange_product_id(self, cr, uid, ids, pricelist, product_id, qty=0, partner_id=False, almacendespacho=False, session_id=False, context=None):        
        context = context or {}
        if not  session_id:
            raise osv.except_osv(_('Error de sesion!'), _('Debe de elegir una,\n sesion antes de ingrsar los productos a vender.'))
                    
        warning = {}      
        warning_msgs = ''

        #Permite enviar el id del almacen de despacho
        c = context.copy()
        if almacendespacho:
            c.update({'location': almacendespacho })
        else:
            session = self.pool.get('pos.session').browse(cr, uid, session_id) 
            c.update({'location': session.config_id.shop_id.warehouse_id.lot_stock_id.id })            
        #Fin

        if not product_id:
            return {}
        if not pricelist:
            raise osv.except_osv(_('No Pricelist!'),_('You have to select a pricelist in the sale form !\n' \
               'Please set one before choosing a product.'))

        #PERMITE VER SI LA CANTIDAD A VENDER ES PERMITIDA PARA PRODUCTOS IMPORTADOS
        prod_id = self.pool.get('product.product').browse(cr, uid, product_id, context=c)        
        if almacendespacho:
            #if prod_id.procedencia == 'import':
            if prod_id.qty_disponible < qty:
                warn_msg = _(('No puede vender un producto importado del almacen PRINCIPAL con stock insuficiente, Producto: "%s" (Cant. Dispo:%d).')  %(prod_id.name, prod_id.qty_disponible,))
                warning_msgs += _("Stock insuficiente ! : ") + warn_msg +"\n\n"
        else:
            if prod_id.qty_disponible < qty:
                warn_msg = _(('No puede vender un producto con stock insuficiente, Producto: "%s" (Cant. Dispo:%d).') %(prod_id.name, prod_id.qty_disponible,))
                warning_msgs += _("Stock insuficiente ! : ") + warn_msg +"\n\n"
        #FIN        

        price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],product_id, qty or 1.0, partner_id)[pricelist]
        result = self.onchange_qty(cr, uid, ids, product_id, 0.0, qty, price, almacendespacho, session_id, context=c)
        result['price_unit'] = price

        if warning_msgs:
            warning = {
                       'title': ('Error de STOCK!'),
                       'message' : warning_msgs
                    }        

        return {'value': result,'warning': warning}


    def onchange_qty(self, cr, uid, ids, product, discount, qty, price_unit, almacendespacho=False, session_id=False, context=None):
        context = context or {}
        if not  session_id:
            raise osv.except_osv(_('Error de sesion!'), _('Debe de elegir una,\n sesion antes de ingrsar los productos a vender.'))

        result = {}
        warning = {}
        warning_msgs = ''
        
        #Permite enviar el id del almacen de despacho
        c = context.copy()
        
        #almacendesp =None
        if almacendespacho:
            c.update({'location': almacendespacho })
            #almacendesp =  almacendespacho
        else:
            if session_id:
                session = self.pool.get('pos.session').browse(cr, uid, session_id)
                #_logger.error("PINCK_CONTEXT22222: %r", session_id) 
                c.update({'location': session.config_id.shop_id.warehouse_id.lot_stock_id.id })
        #Fin

        if not product:
            return result
        account_tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')

        prod = self.pool.get('product.product').browse(cr, uid, product, context=c)

        price = price_unit * (1 - (discount or 0.0) / 100.0)
        taxes = account_tax_obj.compute_all(cr, uid, prod.taxes_id, price, qty, product=prod, partner=False)
        

        result['price_subtotal'] = taxes['total']
        result['price_subtotal_incl'] = taxes['total_included']

        #PERMITE VER SI LA CANTIDAD A VENDER ES PERMITIDA 
             
        #_logger.error("PINCK_CONTEXT1: %r", almacendesp)        
        if almacendespacho:
            #if prod.procedencia == 'import':
            if prod.qty_disponible < qty:
                warn_msg = _(('No puede vender un producto importado del almacen PRINCIPAL con stock insuficiente, Producto: "%s" (Cant. Dispo:%d).')  %(prod.name, prod.qty_disponible,))
                warning_msgs += _("Stock insuficiente ! : ") + warn_msg +"\n\n"
        else:
            if prod.qty_disponible < qty:
                warn_msg = _(('No puede vender un producto con stock insuficiente, Producto: "%s" (Cant. Dispo:%d).') %(prod.name, prod.qty_disponible,))
                warning_msgs += _("Stock insuficiente ! : ") + warn_msg +"\n\n"
            
        #FIN

        if warning_msgs:
            warning = {
                       'title': ('Error de STOCK!'),
                       'message' : warning_msgs
                    }


        return {'value': result, 'warning': warning}


