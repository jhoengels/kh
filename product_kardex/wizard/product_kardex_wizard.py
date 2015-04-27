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


from openerp.osv import fields, osv
import time,dateutil, dateutil.tz
from dateutil.relativedelta import relativedelta

from datetime import date, datetime

import logging
_logger = logging.getLogger(__name__)

class product_kardex_wizard(osv.osv_memory):
#    _inherit = "account.common.journal.report"
    _name = 'product.kardex.wizard'
    _description = 'Imprime el kardex de un producto'

    _columns = {
        'location_ids': fields.many2one('stock.location', 'Ubicacion', required="True"),
        'product_ids': fields.many2one('product.product', 'Producto'),
        'fecha_desde': fields.date('Desde'),
        'fecha_hasta': fields.date('Hasta'),
    }

    _defaults = {
    	'fecha_desde': fields.date.context_today,
    	'fecha_hasta': fields.date.context_today,
    }

    def print_report(self, cr, uid, ids, context=None):
        datas = {}
        if context is None:
            context = {}

#        datas = {'ids': context.get('active_ids', [])} #
        res = self.read(cr, uid, ids, ['product_ids','location_ids','fecha_desde','fecha_hasta'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
#        if res.get('id',False): #
#           datas['ids']=[res['name_id']]#
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'kardex.product',
            'datas': datas,
        }


    def print_report_xls(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        form={} #
        data = self.read(cr, uid, ids)[0]  #RECIBIMOS LOS DATOS DEL FORMULARIO     
        producto_id = data['product_ids'][0] # OBETENEMOS SOLO EL ID DEL PRODUCTO
        location_id = data['location_ids'][0]

        form.update({
            'producto_id': producto_id, 
            'location_id': location_id,        
            'fecha_desde': data['fecha_desde'],
            'fecha_hasta': data['fecha_hasta'],
        })

        _logger.error("PINCKING 1: %r", form)
        
        if context.get('xls_export'):
            return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'kardex.product.xls',#El nombre por defecto del archivo xls generado
                    'datas': form
            }
        #else:
        #    return {
        #        'type': 'ir.actions.report.xml',
        #        'report_name': 'account.partner.open.arap.period.print',
        #        'datas': data}

    def print_report_cal(self, cr, uid, ids, context=None):
        return self.print_report_xls(cr, uid, ids, context=context)

product_kardex_wizard()




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
