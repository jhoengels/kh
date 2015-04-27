# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 SC. (http://salazarcarlos.com).
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

from openerp.osv import fields, osv, orm
from openerp import tools
import logging
_logger = logging.getLogger(__name__)

class tipo_documento_sequence_wizard(osv.osv_memory):
    _name = "tipo.documento.sequence.wizard"
    _columns = {
        'sequence_id' : fields.many2one('ir.sequence', 'Secuencia'),
        'next_number' : fields.char('Siguiente numero'),
    }
    def onchange_sequence_id(self, cr, uid, ids, sequence_id, context=None):        
        if sequence_id:
            sequence = self.pool.get('ir.sequence').browse(cr, uid, sequence_id, context=context)
            return {'value': {'next_number': sequence.number_next_actual}}
        return {'value': {'next_number': 0}}

    def update_sequence(self, cr, uid, ids, context=None):
        sequence_obj = self.pool.get('ir.sequence')        
        wizard = self.browse(cr, uid, ids[0], context)
        #_logger.error("updateee: %r", wizard.next_number) 
        sequence_obj.write(cr, uid, wizard.sequence_id.id, {'number_next_actual': wizard.next_number})

        return True
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
