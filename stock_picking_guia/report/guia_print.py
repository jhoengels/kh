# -*- encoding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (c) 2013 SysNeo Consulting SAC. (http://sysneoconsulting.com).
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
import time

from stock.report import picking

from report import report_sxw

from tools.translate import _

class picking_print(picking.picking):
    def __init__(self, cr, uid, name, context):
        super(picking_print, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_product_desc': self.get_product_desc,
            'get_qtytotal':self._get_qtytotal,
        })

    #Para obtener el total de productos en la GR
    def _get_qtytotal(self,move_lines):
        total = 0.0
        uom = move_lines[0].product_uom.name
        for move in move_lines:
            total+=move.product_qty
        return {'quantity':total,'uom':uom}

from netsvc import Service
del Service._services['report.stock.picking.list']
del Service._services['report.stock.picking.list.in'] 
del Service._services['report.stock.picking.list.out'] 

for suffix in ['', '.in', '.out']:
    report_sxw.report_sxw('report.stock.picking.list' + suffix,
                          'stock.picking' + suffix,
                          'addons/stock/report/picking.rml',
                          parser=picking_print,header=False)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

