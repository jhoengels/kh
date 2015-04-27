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

from report import report_sxw

from tools.translate import _

class account_voucher_print(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(account_voucher_print, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
        })

report_sxw.report_sxw(
    'report.account.print.voucher', #se poner report + el monbre del reporte
    'account.voucher',
    'addons/account_voucher_print/report/account_voucher_print.rml',
    parser=account_voucher_print,
    header=False
)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

