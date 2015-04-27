# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP s.a. (<http://www.openerp.com>).
#    Copyright (C) 2012-TODAY Mentis d.o.o. (<http://www.mentis.si/openerp>)
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

from osv import osv, fields
import logging
_logger = logging.getLogger(__name__)

class stock_picking_in(osv.osv):
    _inherit = "stock.picking.in"

    _columns = {
        'valorizado': fields.boolean('Valorizado'),
        'facturado': fields.boolean('Facturado'),
        'landing_costs_line_ids': fields.one2many('purchase.landing.cost.position', 'picking_id', 'Landing Costs'),
    }

    def valorizar(self, cr, uid, ids, context=None):

        pickings = self.browse(cr, uid, ids, context=context)
      
        product_obj = self.pool.get('product.product')

        for picking in pickings:
            if picking.valorizado == False:
                for r in picking.move_lines:
                    product = product_obj.browse(cr, uid, r.product_id.id)
                    #_logger.error("PRODUC QTY----: %r", product.qty_available-r.product_qty)                    
                    #if product.qty_available-r.product_qty <= 0:
                    #    product.qty_available = 0
                    amount_unit = product.price_get('standard_price', context=context)[product.id]
                    if amount_unit == 0.0:
                    	amount_unit = 1.0                   
                    new_std_price = ((amount_unit * (product.qty_available-r.product_qty)) + (r.price_unit_with_costs * r.product_qty))/((product.qty_available-r.product_qty) + r.product_qty)
                    #_logger.error("PRECIO UNIT----: %r", new_std_price )

                    #product_obj.write(cr, uid, [r.product_id.id], {'standard_price': r.price_unit_with_costs})
                    
                    product_obj.write(cr, uid, [r.product_id.id], {'standard_price': new_std_price})
           	picking.write({'valorizado': True}, context=context)
        return True

    def _prepare_landed_cost_inv_line(self, cr, uid, account_id, inv_id, landed_cost, context=None):
        """ Collects require data from landed cost position that is used to
        create invoice line for that particular position.

        If it comes from a PO line and Distribution type is per unit
        the quantity of the invoice is the PO line quantity

        :param account_id: Expense account.
        :param inv_id: Related invoice.
        :param browse_record landed_cost: Landed cost position browse record
        :return: Value for fields of invoice lines.
        :rtype: dict

        """
        qty = 1.0
        
        line_tax_ids = [x.id for x in landed_cost.product_id.supplier_taxes_id]
        return {
            'name': landed_cost.product_id.name,
            'account_id': account_id,
            'invoice_id': inv_id,
            'price_unit': landed_cost.amount or 0.0,
            'quantity': qty,
            'product_id': landed_cost.product_id.id or False,
            'uos_id': landed_cost.product_id.uom_id.id,
            'invoice_line_tax_id': [(6, 0, line_tax_ids)],
        }

    def _prepare_landed_cost_inv(self, cr, uid, landed_cost, context=None):

        currency_id = landed_cost.partner_id.property_product_pricelist_purchase.currency_id.id
        po = landed_cost.picking_id.purchase_id
        fiscal_position_id = landed_cost.partner_id.property_account_position.id
        journal_obj = self.pool.get('account.journal')
        journal_ids = journal_obj.search(cr, uid,[('type', '=', 'purchase'),('company_id', '=', landed_cost.picking_id.company_id.id)],limit=1)
        if not journal_ids:
            raise orm.except_orm(_('Error!'),_('Define purchase journal for this company: "%s" (id: %d).') % (landed_cost.picking_id.company_id.name, landed_cost.picking_id.company_id.id))
        #_logger.error("DIRARIO_id-22---: %r", journal_ids)
        return {
            'currency_id': landed_cost.currency_id.id or currency_id,
            'supplier_invoice_number': landed_cost.num_doc or False,
            'date_invoice': landed_cost.fecha or False,
            'partner_id': landed_cost.partner_id.id,
            'account_id': landed_cost.partner_id.property_account_payable.id,
            'type': 'in_invoice',
            'origin': landed_cost.picking_id.name + ':' + po.name or False,
            'fiscal_position': fiscal_position_id,
            'company_id': landed_cost.picking_id.company_id.id or False,
            'journal_id': len(journal_ids) and journal_ids[0] or False,
        }

    def _generate_invoice_from_landed_cost(self, cr, uid, landed_cost, context=None):
        """ Generate an invoice from order landed costs (means generic
        costs to a whole PO) or from a line landed costs.

        """
        invoice_obj = self.pool.get('account.invoice')
        invoice_line_obj = self.pool.get('account.invoice.line')
        prod_obj = self.pool.get('product.product')

        vals_inv = self._prepare_landed_cost_inv(cr, uid, landed_cost, context=context)
        inv_id = invoice_obj.create(cr, uid, vals_inv, context=context)
        #_logger.error("INVOICE-22---: %r", inv_id)
        account_id = landed_cost.product_id.categ_id.property_account_expense_categ.id
        #_logger.error("INVOICE-22---: %r", account_id)
        vals_line = self._prepare_landed_cost_inv_line(cr, uid, account_id, inv_id, landed_cost, context=context)
        invoice_line_obj.create(cr, uid, vals_line, context=context)
        return inv_id

    def create_invoice_landcost(self, cr, uid, ids, context=None):
        for picking in self.browse(cr, uid, ids, context=context):
            invoice_ids = []
            if picking.facturado == False:
                for picking_cost in picking.landing_costs_line_ids:                  
                    #_logger.error("COST----: %r", picking_cost)
                    if picking_cost.is_invoiced:
                        inv_id = self._generate_invoice_from_landed_cost(cr, uid, picking_cost, context=context)
                        invoice_ids.append(inv_id)
                picking.write({'facturado': True}, context=context)
        return True
