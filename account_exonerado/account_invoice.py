# -*- coding: utf-8 -*-

from openerp.osv import osv,fields
import netsvc
from openerp import netsvc
import openerp.addons.decimal_precision as dp

class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    def _exonerado(self, cr, uid, ids, field, arg, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            exo=0.0
            for line in invoice.invoice_line:
                if not line.invoice_line_tax_id:
                    exo += line.price_subtotal
        res[invoice.id] = exo
        return res
    _columns = {
        'exonerado': fields.function(_exonerado,digits_compute=dp.get_precision('Account'), string='Exonerado de IGV',method=True,store=True)
        }
