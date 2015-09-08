# -*- encoding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (c) 2015 SC. (http://salazarcarlos.com).
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

from osv import osv, fields, orm
import time

import logging
_logger = logging.getLogger(__name__)

class account_invoice(osv.osv):

    _inherit = 'account.invoice'
    _columns = {
        'next_sequence': fields.char("Next sequence", help="Secuencia que será creada en el documento al validar"),
        }

    def onchange_journal_id(self, cr, uid, ids, journal_id=False, context=None):

    	result = {}
        result = super(account_invoice, self).onchange_journal_id(cr, uid, ids, journal_id, context)
        journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
        next_number = "[%r]" % journal.sequence_id.number_next_actual

        result['value'].update({'next_sequence':next_number})
        return result
    '''
    def onchange_next_sequence(self, cr, uid, ids, next_sequence=False, context=None):

        result = {}
        inv_ids = self.pool.get('account.invoice').search(cr, uid, [('next_sequence', '=', next_sequence)], context=context)
        inv = self.pool.get('account.invoice').browse(cr, uid, inv_ids, context=context)

        _logger.error("Invoice 1s: %r", inv_ids)

        #journal = self.pool.get('account.journal').browse(cr, uid, inv[0].journal_id.id, context=context)
        next_number = inv[0].journal_id.sequence_id.number_next_actual
        
        if next_sequence == next_number:
            return True
        else:
            self.pool.get('ir.sequence').write(cr, uid, inv[0].journal_id.sequence_id.id, {'number_next_actual': next_sequence})
            
            return True
    '''