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

from openerp.osv import osv,fields,orm
from openerp import netsvc
from datetime import datetime
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

import logging
_logger = logging.getLogger(__name__)


class sale_cotizacion(osv.osv):
    _name = 'sale.cotizacion'

    def _amount_total(self, cr, uid, ids, name, args, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            #res[order.id] = {'i_total': 0}
            val=0.0
            for line in order.cotizacion_line:  
                #_logger.error("COTIZACION 2---: %r", line.price_subtotal )              
                val+= line.price_subtotal           
            res[order.id] = val
        return res
    def _amount_total_dscto_blobal(self, cr, uid, ids, name, args, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            #res[order.id] = {'i_total': 0}
            val=0.0
            #for line in order.cotizacion_line:  
                #_logger.error("COTIZACION 2---: %r", line.price_subtotal )              
            #    val+= line.price_subtotal  
            res[order.id] = order.total * (1 - order.dscto_global /100.0)
        return res

    def _amount_total_dolar(self, cr, uid, ids, name, args, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):          
            res[order.id] = order.total / order.tipo_cambio
        return res

    _columns = {
        'name': fields.char('Order Reference', size=64, required=True, select=True),        
        'date_order': fields.date('Fecha', required=True, select=True,),
        'user_id': fields.many2one('res.users', 'Asesor corporativo', select=True, track_visibility='onchange'),
        'partner_id': fields.many2one('res.partner', 'Cliente', readonly=False, required=True, change_default=True, select=True, track_visibility='always'),
        'cotizacion_line': fields.one2many('sale.cotizacion.line', 'cotizacion_id', 'Lineas Cotizacion',),
        'order_ids': fields.one2many('sale.order', 'cotizacion_id', 'Order relacionados', readonly=False, ),
        'note': fields.text('Terminos y condiciones'),
        'shop_id': fields.many2one('sale.shop', 'Tienda', required=True, ),

        'partner_shipping_id': fields.many2one('res.partner', 'Direccion de entrega', ),
        'partner_contact_id': fields.many2one('res.partner', 'Direccion de Contacto', ),
        'pricelist_id': fields.many2one('product.pricelist', 'Lista de precio', ),
        'currency_id': fields.related('pricelist_id', 'currency_id', type="many2one", relation="res.currency", string="Moneda",),
        'forma_pago': fields.selection([('contado','Contado'),('credito','Credito')],'Forma de pago'),
        'payment_term': fields.many2one('account.payment.term', 'Plazo de pago'),
        'igv': fields.selection([('con_igv','Incluye IGV'),('sin_igv','No Incluye IGV')], 'Impuesto 18%'),
        'flete': fields.selection([('con_flete','Incluido Flete'),('sin_flete','No Incluye Flete')],'Flete'),
        'embalaje': fields.selection([('con_embalaje','Incluido Embalaje'),('sin_embalaje','No Incluye Embalaje')],'Embalaje'),
        'fecha_expected': fields.datetime('Fecha entrega al cliente', select=True, ),
        'tipo_entrega': fields.selection([('dentro_ciudad','Dentro de Ciudad'),('recojo_agencia','Recojo en Agencia'),('recojo_tienda','Recojo en Tienda')],'Tipo Entrega'),
        'tipo_cambio': fields.float('Tipo de Cambio', digits_compute= dp.get_precision('Product Price'),),     
        'total_dolar': fields.function(_amount_total_dolar, string='Total Dolar', digits_compute= dp.get_precision('Account'), method=True, type='float'),
        'costo_flete': fields.float('Costo de Flete(S/.)', digits_compute= dp.get_precision('Product Price'),),
        'costo_embalaje': fields.float('Costo de embalaje(S/.)', digits_compute= dp.get_precision('Product Price'),),

        'dscto_global': fields.float('Dscto global(%)', digits_compute= dp.get_precision('Discount'),),
        'total': fields.function(_amount_total, string='Total', digits_compute= dp.get_precision('Account'), method=True, type='float'),        
        'total_dscto_global': fields.function(_amount_total_dscto_blobal, string='Total con Dscto', digits_compute= dp.get_precision('Account'), method=True, type='float'),


        }
        
    _defaults = {
        'date_order': fields.date.context_today,
        'user_id': lambda obj, cr, uid, context: uid,
        'name': lambda obj, cr, uid, context: '/',
        'tipo_cambio': 1.0,
        }
    _order='date_order desc'

    def create(self, cr, uid, vals, context=None):
        """Rewrite Create method.
        This method spend new sequence when create (not default value)
        :param vals: dicc
        :return order_id
        """
        if context is None:
            context = {}

        cotizacion_id = super(sale_cotizacion, self).create(cr, uid, vals,context=context)
        ctx = context.copy()

        shop_id = vals.get('shop_id', [])
        shop = self.pool.get('sale.shop').browse(cr, uid, shop_id, context)
        sequence_obj = self.pool.get('ir.sequence')

        #if vals.get('name','/') == '/': #get new sequence
        if shop and shop.sequence_cotiz_id:
            vals = {'name': sequence_obj.get_id(cr, uid, shop.sequence_cotiz_id.id, context=ctx)}
        else:
            raise osv.except_osv(_('Warning!'),_('La tienda no tiene secuencia asignada, crear una secuencia de cotizacion: TIENDA %s') %(shop.name))
        
        self.write(cr, uid, cotizacion_id, vals, context=context)
        return cotizacion_id

    def print_quotation(self, cr, uid, ids, context=None):
        assert len(ids) == 1 
        datas = {
                 'model': 'sale.cotizacion',
                 'ids': ids,
                 'form': self.read(cr, uid, ids[0], context=context),
        }
        return {'type': 'ir.actions.report.xml', 'report_name': 'sale.cotizacion.print', 'datas': datas, 'nodestroy': True}


    def action_order_create(self, cr, uid, ids, context=None):
        for cotizacion in self.browse(cr, uid, ids, context=context):
            self._create_order(cr, uid, cotizacion, cotizacion.cotizacion_line, None, context=context)
        return True

    def _create_order(self, cr, uid, cotizacion, cotizacion_lines, order_id=False, context=None):
        sale_obj = self.pool.get('sale.order')
        sale_line_obj = self.pool.get('sale.order.line')
        order_id = sale_obj.create(cr, uid, self._prepare_order(cr, uid, cotizacion, context=context))
        for line in cotizacion_lines:
            sale_line_id = sale_line_obj.create(cr, uid, self._prepare_order_line(cr, uid, cotizacion, line, order_id, context=context))
        return True

    def _prepare_order(self, cr, uid, cotizacion, context=None):
        part = self.pool.get('res.partner').browse(cr, uid, cotizacion.partner_id.id, context=context)
        addr = self.pool.get('res.partner').address_get(cr, uid, [part.id], ['delivery', 'invoice', 'contact'])
        return {
            'partner_id': cotizacion.partner_id.id,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'cotizacion_id': cotizacion.id,
            'date': cotizacion.date_order,
            'shop_id': cotizacion.shop_id.id,
            'pricelist_id': cotizacion.partner_id.property_product_pricelist.id,
            'currency_id' : cotizacion.currency_id,
            'payment_term': cotizacion.payment_term.id,
            'fecha_expected': cotizacion.fecha_expected,
        }

    def _prepare_order_line(self, cr, uid, cotizacion, line, order_id, context=None):
        return {
            'product_id': line.product_id.id,
            'name': line.name,
            'descripcion_sale_id': line.descripcion_sale_id.id or False,
            'tax_id': [(6, 0, [x.id for x in line.product_id.taxes_id])],
            'product_uom_qty': line.product_uom_qty,
            'price_original': line.price_unit,
            'price_unit': line.price_subtotal/line.product_uom_qty or 0.0,
            'order_partner_id': cotizacion.partner_id.id,
            'order_id': order_id,
            'state': 'draft',            
        }

    def action_view_order(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.get_object_reference(cr, uid, 'sale', 'action_quotations')        
        id = result and result[1] or False        
        result = act_obj.read(cr, uid, [id], context=context)[0]
        #compute the number of orders to display
        order_ids = []
        for so in self.browse(cr, uid, ids, context=context):
            order_ids += [order.id for order in so.order_ids]            
        result['domain'] = "[('id','in',["+','.join(map(str, order_ids))+"])]"
        #_logger.error("COTIZACION 3---: %r", order_ids)
        return result

    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        if not partner_id:
            return {'value': {'partner_shipping_id': False,  'payment_term': False, 'partner_contact_id':False}}

        partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
        addr = self.pool.get('res.partner').address_get(cr, uid, [partner.id], ['delivery', 'invoice', 'contact'])
        pricelist = partner.property_product_pricelist and partner.property_product_pricelist.id or False
        payment_term = partner.property_payment_term and partner.property_payment_term.id or False
        dedicated_salesman = partner.user_id and partner.user_id.id or uid
        val = {
            'partner_shipping_id': addr['delivery'],
            'partner_contact_id': addr['contact'],
            'payment_term': payment_term,
            'user_id': dedicated_salesman,
        }
        if pricelist:
            val['pricelist_id'] = pricelist
        return {'value': val}

    def onchange_pricelist_id(self, cr, uid, ids, pricelist_id, cotizacion_lines, context=None):
        context = context or {}
        if not pricelist_id:
            return {}
        value = {
            'currency_id': self.pool.get('product.pricelist').browse(cr, uid, pricelist_id, context=context).currency_id.id
        }
        #_logger.error("COTIZACION 3---: %r", value)
        if not cotizacion_lines:
            return {'value': value}
        warning = {
            'title': _('Pricelist Warning!'),
            'message' : _('If you change the pricelist of this order (and eventually the currency), prices of existing order lines will not be updated.')
        }

        return {'warning': warning, 'value': value}

    def button_dummy(self, cr, uid, ids, context=None):
        return True


class sale_cotizacion_line(osv.osv):
    _name = 'sale.cotizacion.line'

    def _price_subtotal(self, cr, uid, ids, name, args, context=None):
        res = dict([(i, {}) for i in ids])
        for line in self.browse(cr, uid, ids, context=context):
            
            price = (line.price_unit*(1 - line.dscto_unit/100.0)  + line.flete*line.cotizacion_id.costo_flete/100.0 + line.embalaje*line.cotizacion_id.costo_embalaje/100.0)*line.product_uom_qty
            #price = line.price_unit_venta * line.product_uom_qty
            _logger.error("SUB TOTALLL 1---: %r", price)
            res[line.id] = price
        return res

    def onchange_product_id(self, cr, uid, ids, product_id, qty=0, name='', context=None):
        context = context or {}
        result = {}
        if not product_id:
            return {}
        product = self.pool.get('product.product').browse(cr, uid, product_id, context)
        #_logger.error("COTIZACION 3---: %r", product_obj.name)
        result['name'] = product.name
        result['price_unit'] = product.list_price

        return {'value': result }

    _columns = {
        'cotizacion_id': fields.many2one('sale.cotizacion', 'Cotizacion de referencia', ondelete='cascade',),
        'product_id': fields.many2one('product.product', 'Producto', domain=[('sale_ok', '=', True)],),
        'descripcion_sale_id': fields.many2one('product.descripcion', string="Descripciones"),
        'name': fields.text('Descripcion', required=True, readonly=False,),

        'product_uom_qty': fields.float('Cant.', digits_compute= dp.get_precision('Product UoS'), required=True, readonly=False,),
        'price_unit': fields.float('Precio U.', required=True, digits_compute= dp.get_precision('Product Price'), readonly=False,),

        'dscto_unit': fields.float('Dscto Unit(%)', digits_compute= dp.get_precision('Discount'),),
        'price_unit_dscto': fields.float('P.U. Dscto.', digits_compute= dp.get_precision('Product Price'), readonly=False,),

        'flete': fields.float('Flete(%)', digits_compute= dp.get_precision('Discount'), ),
        'embalaje': fields.float('Embalaje(%)', digits_compute= dp.get_precision('Discount'), ),
                
        #'price_unit_venta': fields.function(_price_unit_venta,string='P.U. Venta', required=True, digits_compute= dp.get_precision('Product Price'), store=True),
        'price_unit_venta': fields.float(string='P.U. Venta', required=True, digits_compute= dp.get_precision('Product Price') ),
        'price_subtotal': fields.function(_price_subtotal, string='Subtotal', digits_compute= dp.get_precision('Account'), store=False),
       } 
    _defaults = {
        'product_uom_qty': 1.0,
        'price_unit': 0.0,
        'dscto_unit': 0.0,
        }
    
    def onchange_descripcion(self,cr,uid,ids,descripcion_sale_id,product_id,name='',context=None):
        res = {}
        if descripcion_sale_id:
            prod = self.pool.get('product.descripcion').name_get(cr,uid,descripcion_sale_id,context=context)[0][1]
            return {'value': {'name': prod}}
        product = self.pool.get('product.product').browse(cr, uid, product_id, context)
        return {'value': {'name': product.name }}

    def onchange_dscto_unit(self, cr, uid, ids, price_unit, dscto_unit, context=None):        
        value = {}
        value['price_unit_dscto'] = price_unit*(1 - dscto_unit/100.0)
        #_logger.error("COTIZACION 1---: %r", dscto_unit/100.0)
        return {'value': value}

    def onchange_price_unit_dscto(self, cr, uid, ids, costo_flete, costo_embalaje, price_unit_dscto, flete, embalaje, context=None):        
        value = {}
        value['price_unit_venta'] = price_unit_dscto + flete*costo_flete/100.0 + embalaje*costo_embalaje/100.0
        #_logger.error("COTIZACION 1---: %r", costo_flete)
        return {'value': value}


class sale_order(osv.osv):
    _inherit = 'sale.order'
    _columns = {
        'cotizacion_id': fields.many2one('sale.cotizacion', 'Sales Contizacion', ondelete='set null', select=True),
    }
    _defaults = {
        'cotizacion_id': False
    }

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    _columns = {
        'price_original': fields.float('Precio original', digits_compute= dp.get_precision('Product Price'), ),
    }

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0, uom=False, qty_uos=0, uos=False, name='', partner_id=False, lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        
        if not product:
            return True
        val = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name, partner_id, lang, update_tax, date_order, packaging, fiscal_position, flag , context)
        #_logger.error("CAMBIADO PRODUCTO---: %r", product)
        res = val['value']
        product_obj = self.pool.get('product.product').browse(cr, uid, product, context=context)
        res.update({
               'price_original': product_obj.list_price or 0.0,
            })
        #_logger.error("CAMBIADO PRODUCTO---: %r", val)
        return val


class sale_shop(osv.osv):
    _inherit = "sale.shop"
    _columns = {
        'sequence_cotiz_id': fields.many2one('ir.sequence', "Secuencia Cotizacion", help="La secuencia utilizada para la elaboracionde cotizacion."),
    }



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: