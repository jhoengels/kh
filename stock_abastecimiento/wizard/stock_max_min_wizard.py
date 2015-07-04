# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 S&C (<http://salazarcarlos.com>).
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

from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp

import logging

_logger = logging.getLogger(__name__)

class stock_abastecimiento_wizard(osv.osv_memory):
    _name = 'stock.max.min.wizard'
    _columns = {
        'product_ids': fields.many2many('product.product', 'stock_abastecimiento_product_rel', 'product_id', 'wizard_id', 'Producto stock max min'), 
    }
    def agregar_productos(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['product_ids'], context=context)
        res = res and res[0] or {}        
        stock_max_min_line_obj = self.pool.get('stock.max.min.line')
        for product_id in res['product_ids']:
        	vals = {'max_min_id':datas['ids'][0],'product_id': product_id}
        	#_logger.error("INNNNNN111111: %r", context)
        	stock_max_min_line_obj.create(cr, uid, vals)
        return True



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: