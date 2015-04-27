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

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time

from osv import osv, fields
import netsvc
from tools.translate import _
import decimal_precision as dp



class sale_order(osv.osv):
    _inherit = 'sale.order'
    _columns = {
        'ruc_dni': fields.char('RUC/DNI',size=32, states={'manual':[('readonly',True)], 'progress':[('readonly',True)],'done':[('readonly',True)]}, )
        }

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        if not part:
            return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False,  'payment_term': False, 'fiscal_position': False, 'ruc_dni': False}}

        val = super(sale_order, self).onchange_partner_id(cr, uid, ids, part, context)
        value = val['value']
        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        value.update({
               'ruc_dni': part.doc_number,
            })
        return {'value': value}

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        if context is None:
            context = {}

        invoice_vals = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context)
        invoice_vals.update({
                'ruc_dni': order.ruc_dni or '', #agregado nuevos cambios
                'shop_id': order.shop_id.id or '',
            })

        return invoice_vals
    
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
            return {'value': {'partner_id': False, 'partner_shipping_id': False,  'payment_term': False, 'fiscal_position': False, 'ruc_dni': False}}

sale_order()



class account_invoice(osv.osv):
    _name = "account.invoice"
    _inherit = 'account.invoice'
    _columns = {
	'ruc_dni': fields.char('RUC/DNI',size=32, states={'paid':[('readonly', True)], 'open':[('readonly', True)], 'cancel':[('readonly',True)]},),
    'fact_ref': fields.char('FACTURA REF',size=32, states={'paid':[('readonly', True)], 'open':[('readonly', True)],  'cancel':[('readonly',True)]},),
        'shop_id': fields.many2one('sale.shop', 'Shop', help='Relaciona la factura actual con la tienda'),   
        }

    def onchange_partner_id(self, cr, uid, ids, type, partner_id, date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        val =  super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id, date_invoice, payment_term, partner_bank_id, company_id)
        result = val['value']
        p = self.pool.get('res.partner').browse(cr, uid, partner_id)
        if partner_id:
            result.update({
                   'ruc_dni': p.doc_number or p.parent_id.doc_number,# agregado nuevos cambios                   
                })
        return {'value': result}


    def _prepare_refund(self, cr, uid, invoice, date=None, period_id=None, description=None, journal_id=None, ruc_dni=None, fact_ref=None,context=None):
        """Prepare the dict of values to create the new refund from the invoice.
            This method may be overridden to implement custom
            refund generation (making sure to call super() to establish
            a clean extension chain).

            :param integer invoice_id: id of the invoice to refund
            :param dict invoice: read of the invoice to refund
            :param string date: refund creation date from the wizard
            :param integer period_id: force account.period from the wizard
            :param string description: description of the refund from the wizard
            :param integer journal_id: account.journal from the wizard
            :return: dict of value to create() the refund
        """
        obj_journal = self.pool.get('account.journal')

        type_dict = {
            'out_invoice': 'out_refund', # Customer Invoice
            'in_invoice': 'in_refund',   # Supplier Invoice
            'out_refund': 'out_invoice', # Customer Refund
            'in_refund': 'in_invoice',   # Supplier Refund
        }
        invoice_data = {}
        for field in ['name', 'reference', 'comment', 'date_due', 'partner_id', 'company_id',
                'account_id', 'currency_id', 'payment_term', 'user_id', 'fiscal_position']:
            if invoice._all_columns[field].column._type == 'many2one':
                invoice_data[field] = invoice[field].id
            else:
                invoice_data[field] = invoice[field] if invoice[field] else False

        invoice_lines = self._refund_cleanup_lines(cr, uid, invoice.invoice_line, context=context)

        tax_lines = filter(lambda l: l['manual'], invoice.tax_line)
        tax_lines = self._refund_cleanup_lines(cr, uid, tax_lines, context=context)
        if journal_id:
            refund_journal_ids = [journal_id]
        elif invoice['type'] == 'in_invoice':
            refund_journal_ids = obj_journal.search(cr, uid, [('type','=','purchase_refund')], context=context)
        else:
            refund_journal_ids = obj_journal.search(cr, uid, [('type','=','sale_refund')], context=context)

        if not date:
            date = fields.date.context_today(self, cr, uid, context=context)
        invoice_data.update({
            'type': type_dict[invoice['type']],
            'date_invoice': date,
            'state': 'draft',
            'number': False,
            'ruc_dni': ruc_dni,#para coger RUC_DNI en la Note de credito
            'fact_ref': fact_ref,
            'invoice_line': invoice_lines,
            'tax_line': tax_lines,
            'journal_id': refund_journal_ids and refund_journal_ids[0] or False,
        })
        if period_id:
            invoice_data['period_id'] = period_id
        if description:
            invoice_data['name'] = description
        return invoice_data


    def refund(self, cr, uid, ids, date=None, period_id=None, description=None, journal_id=None, context=None):
        new_ids = []
        for invoice in self.browse(cr, uid, ids, context=context):

            invoice = self._prepare_refund(cr, uid, invoice,
                                                date=date,
                                                period_id=period_id,
                                                description=description,
                                                journal_id=journal_id,
                                                ruc_dni=invoice.ruc_dni or invoice.partner_id.parent_id.doc_number, #para coger autom. los correlatvos
                                                fact_ref = invoice.number,
                                                context=context)
            # create the new invoice
            new_ids.append(self.create(cr, uid, invoice, context=context))

        return new_ids

    def action_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        account_move_obj = self.pool.get('account.move')
        invoices = self.read(cr, uid, ids, ['move_id', 'payment_ids'])
        move_ids = [] # ones that we will need to remove
        for i in invoices:
            if i['move_id']:
                move_ids.append(i['move_id'][0])
            if i['payment_ids']:
                account_move_line_obj = self.pool.get('account.move.line')
                pay_ids = account_move_line_obj.browse(cr, uid, i['payment_ids'])
                for move_line in pay_ids:
                    if move_line.reconcile_partial_id and move_line.reconcile_partial_id.line_partial_ids:
                        raise osv.except_osv(_('Error!'), _('You cannot cancel an invoice which is partially paid. You need to unreconcile related payment entries first.'))       

        # Agregado para poner en 0 los montos de la factura               
        for id in ids:
            #_logger.error("INOICE CANCELAR---: %r", id)
            cr.execute('UPDATE account_invoice SET amount_total=0.0, amount_tax=0.0, amount_untaxed=0.0, exonerado=0.0 WHERE id=%s', (id,))
            #cr.execute("""update account_invoice set amount_total=0, amount_tax=0, amount_untaxed=0, exonerado=0 where id=%s""", (id,))
        #fin

        # First, set the invoices as cancelled and detach the move ids
        self.write(cr, uid, ids, {'state':'cancel', 'move_id':False,})

        if move_ids:
            # second, invalidate the move(s)
            account_move_obj.button_cancel(cr, uid, move_ids, context=context)
            # delete the move this invoice was pointing to
            # Note that the corresponding move_lines and move_reconciles
            # will be automatically deleted too
            account_move_obj.unlink(cr, uid, move_ids, context=context)
        self._log_event(cr, uid, ids, -1.0, 'Cancel Invoice')
        return True


account_invoice()


class stock_picking(osv.osv):
    _name = "stock.picking"
    _inherit = "stock.picking"

    def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):

        if isinstance(partner, int):
            partner = self.pool.get('res.partner').browse(cr, uid, partner, context=context)
        if inv_type in ('out_invoice', 'out_refund'):
            account_id = partner.property_account_receivable.id
            payment_term = partner.property_payment_term.id or False
        else:
            account_id = partner.property_account_payable.id
            payment_term = partner.property_supplier_payment_term.id or False
        comment = self._get_comment_invoice(cr, uid, picking)

        ########
        fact_ref = None
        ruc_dni = None        
        sale_obj = self.pool.get('sale.order')
        invoice_obj = self.pool.get('account.invoice')
        
        if picking.origin:
            sale_order_id = sale_obj.search(cr,uid,[('name','=',picking.origin)]) # Obtenemos el id
            for sale in sale_obj.browse(cr, uid, sale_order_id):
                account_invoice_id  = invoice_obj.search(cr,uid,['|',('state','=','open'),('state','=','paid'),('origin','=',sale.name),]) # Obtenemos el id
                if account_invoice_id:
                    for invoice in invoice_obj.browse(cr, uid, account_invoice_id):
                        fact_ref = invoice.number
                        ruc_dni = invoice.ruc_dni
        ########

        invoice_vals = {
            'name': picking.name,
            'origin': (picking.name or '') + (picking.origin and (':' + picking.origin) or ''),
            'type': inv_type,
            'account_id': account_id,
            'partner_id': partner.id,
            'comment': comment,
            'payment_term': payment_term,
            'fiscal_position': partner.property_account_position.id,
            'date_invoice': context.get('date_inv', False),
            'company_id': picking.company_id.id,
            'user_id': uid,
            'fact_ref': fact_ref or False,
            'ruc_dni': ruc_dni or picking.partner_id.doc_number or picking.partner_id.parent_id.doc_number or False,
        }
        cur_id = self.get_currency_id(cr, uid, picking)
        if cur_id:
            invoice_vals['currency_id'] = cur_id
        if journal_id:
            invoice_vals['journal_id'] = journal_id
        return invoice_vals


