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


import time

from openerp import netsvc
from openerp.osv import osv, fields
from openerp.tools.translate import _


class pos_session_opening(osv.osv_memory):
    _inherit = 'pos.session.opening'
    
    def open_ui(self, cr, uid, ids, context=None):
        context = context or {}
        data = self.browse(cr, uid, ids[0], context=context)
        context['active_id'] = data.pos_session_id.id
        return {
            'name': _('Pos order'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'pos.order',
            #'res_id': session_id,
            'view_id': False,
            'type': 'ir.actions.act_window',
        }
    

pos_session_opening()
