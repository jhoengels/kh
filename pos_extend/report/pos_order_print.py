# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import time
from openerp.report import report_sxw
from openerp import pooler
import logging
_logger = logging.getLogger(__name__)

def titlize(journal_name):
    words = journal_name.split()
    while words.pop() != 'journal':
        continue
    return ' '.join(words)

class pos_order_print(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(pos_order_print, self).__init__(cr, uid, name, context=context)

        user = pooler.get_pool(cr.dbname).get('res.users').browse(cr, uid, uid, context=context)
        partner = user.company_id.partner_id

        self.localcontext.update({
            'time': time,
            'disc': self.discount,
            'net': self.netamount,
            'exo': self._exonerado,
            'get_reg_prod_name': self.regalo_product_name,
            'get_reg_prod_vr': self.regalo_product_vr,
            'get_reg_prod_igv': self.regalo_product_igv,
            'tbruto': self.total_bruto,
            'get_journal_amt': self._get_journal_amt,
            'address': partner or False,
            'titlize': titlize
        })

    def netamount(self, order_line_id):
        sql = 'select (qty*price_unit) as net_price from pos_order_line where id = %s'
        self.cr.execute(sql, (order_line_id,))
        res = self.cr.fetchone()
        #_logger.error("ORDER ID 1: %r", res)
        return res[0]

    def _exonerado(self, order_id):
        pos_order_obj = self.pool.get('pos.order')
        #_logger.error("ORDER ID 1: %r", order_id)
        pos_order_id = pos_order_obj.search(self.cr,self.uid,[('id','=',order_id)])
        for pos_line in pos_order_obj.browse(self.cr, self.uid, pos_order_id):
            exo=0.0
            for posline in pos_line.lines:
                if not posline.product_id.taxes_id:
                    exo += posline.price_subtotal            
        return exo

    def discount(self, order_id):
        sql = 'select discount, price_unit, qty from pos_order_line where order_id = %s '
        self.cr.execute(sql, (order_id,))
        res = self.cr.fetchall()
        dsum = 0
        for line in res:
            if line[0] != 0:
                dsum = dsum +(line[2] * (line[0]*line[1]/100))
        #_logger.error("DESCUENTO 1: %r", dsum)
        return dsum
    
    def regalo_product_name(self, order_line_id):
        sql = 'select product_id, price_unit, qty from pos_order_line where id = %s '
        self.cr.execute(sql, (order_line_id,))
        res = self.cr.fetchone()
        if res[1]==0.0:
            product_obj = self.pool.get('product.product')
            product_id = product_obj.search(self.cr,self.uid,[('id','=',res[0])])
            for val in product_obj.browse(self.cr, self.uid, product_id):
                product_name = val.name
            return product_name
        else:
            return False

    def regalo_product_vr(self, order_line_id):
        sql = 'select product_id, price_unit, qty from pos_order_line where id = %s '
        self.cr.execute(sql, (order_line_id,))
        res = self.cr.fetchone()
        if res[1]==0.0:
            product_obj = self.pool.get('product.product')
            product_id = product_obj.search(self.cr,self.uid,[('id','=',res[0])])
            for val in product_obj.browse(self.cr, self.uid, product_id):
                if val.taxes_id:
                    valor_referencial = val.list_price*res[2]/1.18
                else:
                    valor_referencial = val.list_price*res[2]
            return valor_referencial
        else:
            return False

    def regalo_product_igv(self, order_line_id):
        sql = 'select product_id, price_unit, qty from pos_order_line where id = %s '
        self.cr.execute(sql, (order_line_id,))
        res = self.cr.fetchone()
        if res[1]==0.0:
            product_obj = self.pool.get('product.product')
            product_id = product_obj.search(self.cr,self.uid,[('id','=',res[0])])
            for val in product_obj.browse(self.cr, self.uid, product_id):
                if val.taxes_id:
                    igv = (val.list_price*res[2])/1.18*0.18
                else:
                    igv= 0
            return igv
        else:
            return False

    def total_bruto(self, order_id):
        sql = 'select price_unit, qty from pos_order_line where order_id = %s '
        self.cr.execute(sql, (order_id,))
        res = self.cr.fetchall()
        tb = 0
        for line in res:
            tb = tb +(line[0] * line[1])
        #_logger.error("DESCUENTO 1: %r", tb)
        return tb

    def _get_journal_amt(self, order_id):
        data={}
        sql = """ select aj.name,absl.amount as amt from account_bank_statement as abs
                        LEFT JOIN account_bank_statement_line as absl ON abs.id = absl.statement_id
                        LEFT JOIN account_journal as aj ON aj.id = abs.journal_id
                        WHERE absl.pos_statement_id =%d"""%(order_id)
        self.cr.execute(sql)
        data = self.cr.dictfetchall()
        return data

report_sxw.report_sxw('report.pos.order.print.ticket', 'pos.order', 'addons/pos_extend/report/pos_order_print.rml', parser=pos_order_print, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
