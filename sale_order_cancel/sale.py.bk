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

class sale_order(osv.osv):
    _inherit = "sale.order"

    def action_cancel(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        if context is None:
            context = {}
        sale_order_line_obj = self.pool.get('sale.order.line')
        proc_obj = self.pool.get('procurement.order')
        for sale in self.browse(cr, uid, ids, context=context):
            for pick in sale.picking_ids:
                if pick.state not in ('done'):
                    move_obj = self.pool.get('stock.picking')
                    for pick in self.browse(cr,uid,ids, context=context):
                        ids2 = [move.id for move in pick.picking_ids]
                        move_obj.action_cancel(cr,uid, ids2, context)
                if pick.state == 'cancel':
                    for mov in pick.move_lines:
                        proc_ids = proc_obj.search(cr, uid, [('move_id', '=', mov.id)])
                        if proc_ids:
                            for proc in proc_ids:
                                wf_service.trg_validate(uid, 'procurement.order', proc, 'button_check', cr)
            if sale.shop_id.warehouse_id.id == 1:
                for r in self.read(cr,1, ids, ['picking_ids']):
                    for pick in r['picking_ids']:
                        wf_service.trg_validate(1, 'stock.picking', pick, 'button_cancel', cr)
                for r in self.read(cr, 1, ids, ['picking_ids']):
                    for pick in r['picking_ids']:
                        wf_service.trg_validate(1, 'stock.picking', pick, 'button_cancel', cr)		

            for r in self.read(cr, uid, ids, ['picking_ids']):
                for pick in r['picking_ids']:
                    wf_service.trg_validate(uid, 'stock.picking', pick, 'button_cancel', cr)
        return super(sale_order, self).action_cancel(cr, uid, ids, context=context)

sale_order()
