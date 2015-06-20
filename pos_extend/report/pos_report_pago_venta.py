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

class pos_report_pago_venta(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(pos_report_pago_venta, self).__init__(cr, uid, name, context=context)

        user = pooler.get_pool(cr.dbname).get('res.users').browse(cr, uid, uid, context=context)
        partner = user.company_id.partner_id
        
        self.total = 0.0
        self.localcontext.update({
            'time': time,
            'titlize': titlize,
            'getpayments': self._get_payments,
            'gettotal': self._get_total,
        })
    '''    
    def _get_payments(self, form):
        statement_line_obj = self.pool.get("account.bank.statement.line")
        pos_order_obj = self.pool.get("pos.order")
        user_ids = form['user_ids'] or self._get_all_users()
        pos_ids = pos_order_obj.search(self.cr, self.uid, [('date_order','>=',form['date_start'] + ' 00:00:00'),('date_order','<=',form['date_end'] + ' 23:59:59'),('state','in',['paid','invoiced','done']),('user_id','in',user_ids)])
        data={}
        if pos_ids:
            st_line_ids = statement_line_obj.search(self.cr, self.uid, [('pos_statement_id', 'in', pos_ids)])
            if st_line_ids:
                st_id = statement_line_obj.browse(self.cr, self.uid, st_line_ids)
                a_l=[]
                for r in st_id:
                    a_l.append(r['id'])
                self.cr.execute("select aj.name,sum(amount) from account_bank_statement_line as absl,account_bank_statement as abs,account_journal as aj " \
                                "where absl.statement_id = abs.id and abs.journal_id = aj.id  and absl.id IN %s " \
                                "group by aj.name ",(tuple(a_l),))

                data = self.cr.dictfetchall()
                return data
        else:
            return {}
    '''

    def _get_payments(self, session_id):
        statement_obj = self.pool.get('account.bank.statement')
        statement_line_obj = self.pool.get('account.bank.statement.line')
        data=[]
        res = {}
        statement_ids = statement_obj.search(self.cr, self.uid, [('pos_session_id', '=', session_id)])
        #_logger.error("ORDER sesion: %r", statement_ids)
        for id in statement_ids:
            for line_caja in statement_obj.browse(self.cr, self.uid, [id]):
                if line_caja.balance_end > 0.0:
                    transaciones = statement_line_obj.search(self.cr, self.uid, [('statement_id', '=', line_caja.id)])
                    if line_caja.journal_id.name.find(' LA VICTORIA') != -1:
                        res = {
                            'name': line_caja.journal_id.name[:-12],
                            'total_transaccion' : len(transaciones),
                            'sub_total': line_caja.balance_end,
                        }
                        self.total +=line_caja.balance_end
                        data.append(res)
                    if line_caja.journal_id.name.find(' SAN MIGUEL') != -1:
                        res = {
                            'name': line_caja.journal_id.name[:-11],
                            'total_transaccion' : len(transaciones),
                            'sub_total': line_caja.balance_end,
                        }
                        self.total +=line_caja.balance_end
                        data.append(res)
                    if line_caja.journal_id.name.find(' SURCO') != -1:
                        res = {
                            'name': line_caja.journal_id.name[:-6],
                            'total_transaccion' : len(transaciones),
                            'sub_total': line_caja.balance_end,
                        }
                        self.total +=line_caja.balance_end
                        data.append(res)
        return data 

    def _get_total(self):
        return self.total

report_sxw.report_sxw('report.pos.session.pago.venta', 'pos.session', 'addons/pos_extend/report/pos_report_pago_venta.rml', parser=pos_report_pago_venta, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
