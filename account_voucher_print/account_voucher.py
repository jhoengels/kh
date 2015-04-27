# -*- encoding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (c) 2015 S&C. (http://salazarcarlos.com).
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

class account_voucher(osv.osv):
    _inherit = "account.voucher"
    _columns = {
        'user_id': fields.many2one('res.users', 'Usuario', help='Usuario que realizo el pago actual'),
    }
    _defaults = {
        'user_id': lambda obj, cr, uid, context: uid,
   }

    def action_move_line_create(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        voucher_vals = super(account_voucher, self).action_move_line_create(cr, uid, ids, context)
        for voucher in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, [voucher.id], 
                {'user_id': uid,} #Agreado para rellenar el campo usuario
                )
        return True