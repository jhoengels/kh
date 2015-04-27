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

class users(osv.osv):
    _inherit  =  "res.users"
    _columns  =  {
        'shop_ids': fields.many2many('sale.shop', 'shop_user_rel', 'shop_id', 'user_id', "Shops"),
        'shop_id': fields.many2one('sale.shop', 'Shop', help='Tienda relacionada con el usuario actual'),
    }

    def __init__(self, *args):
        super(users, self).__init__(*args)
        if 'shop_id' not in self.SELF_WRITEABLE_FIELDS:
            self.SELF_WRITEABLE_FIELDS.append('shop_id')

users()
