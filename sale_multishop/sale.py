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
from datetime import datetime

class sale_shop(osv.osv):
    _inherit = "sale.shop"
    _columns = {
        'user_ids': fields.many2many('res.users', 'shop_user_rel', 'user_id', 'shop_id', "Usuarios"),
        'sequence_id': fields.many2one('ir.sequence', "Secuencia orden venta", help="La secuencia utilizada para las ordenes de venta."),
        'journal_id': fields.many2one('account.journal', "Diario contable", help="Diario utilizado para las ventas de esta tienda"),
        'journal_ids': fields.many2many('account.journal', 'account_shop_rel', 'shop_id', 'journal_id', "Medios de pago"),
        'shop_address': fields.char('Direccion'),
        'state_id': fields.many2one("res.country.state", 'Departamento/Provincia/Distrito'),
        'shop_telef': fields.char('Telefono'),
    }
sale_shop()

class account_journal(osv.osv):
    _inherit = "account.journal"
    _columns = {
        'shop_ids': fields.many2many('sale.shop', 'account_shop_rel', 'journal_id', 'shop_id', "Tiendas"),
    }
account_journal()



class sale_order(osv.osv):
    _inherit = "sale.order"

    def _shop_get(self, cr, uid, context=None):
        """ To get  Shop  for this order
        @return: Shop id """
        if context is None:
            context = {}
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        if user.shop_id:
            shop_id = user.shop_id.id
        elif user.shop_ids:
            shop_id = user.shop_ids[0].id
        else:
            res = self.pool.get('sale.shop').search(cr, uid, [])
            shop_id = res and res[0] or False
        return shop_id

    def _make_invoice(self, cr, uid, order, lines, context=None):
        """ To make invoice for this shop
        @input: order
        @input: lines
        @return: invoice id  """
        if context is None:
            context = {}
        invoice = self.pool.get('account.invoice')
        invoice_id = super(sale_order, self)._make_invoice(cr, uid, order, lines, context)
        res = self._shop_get(cr, uid, context=context)
        if res:
            shop = self.pool.get('sale.shop').browse(cr, uid, res, context=context)
            if shop.journal_id:
                invoice.write(cr, uid, invoice_id, {'journal_id': shop.journal_id.id}, context)
        return invoice_id

    _defaults = {
        'shop_id': _shop_get,
        'name': lambda *a: '/',
    }

    def create(self, cr, uid, vals, context=None):
        """Rewrite Create method.
        This method spend new sequence when create (not default value)
        :param vals: dicc
        :return order_id
        """
        if context is None:
            context = {}

        order_id = super(sale_order, self).create(cr, uid, vals,context=context)
        date_order = self.browse(cr, uid, order_id, context).date_order
        ctx = context.copy()

        shop_id = vals.get('shop_id', [])
        shop = self.pool.get('sale.shop').browse(cr, uid, shop_id, context)
        sequence_obj = self.pool.get('ir.sequence')

        #if vals.get('name','/') == '/': #get new sequence
        if shop and shop.sequence_id:
            vals = {'name': sequence_obj.get_id(cr, uid, shop.sequence_id.id, context=ctx)}
        else:
            vals = {'name': sequence_obj.get_id(cr, uid, 'sale.order', test='code', context=ctx)}
        self.write(cr, uid, order_id, vals, context=context)
        return order_id

    def _make_invoice(self, cr, uid, order, lines, context=None):
        if context is None:
            context = {}
        invoice_id = super(sale_order, self)._make_invoice(cr, uid, order, lines, context)
        if order and order.shop_id and order.shop_id.journal_id:
            journal_id = order.shop_id.journal_id.id
            self.pool.get('account.invoice').write(cr, uid, invoice_id, {'journal_id': journal_id}, context)
        return invoice_id

sale_order()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: