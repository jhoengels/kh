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

from osv import osv, fields
from tools.translate import _
from datetime import datetime
import time

class product_product(osv.osv):
	_name= 'product.product'
	_inherit = 'product.product'
	_columns = {
		'descripcion_ids': fields.one2many('product.descripcion','product_id',string="Descripciones"),
                'product_contenido': fields.text('Producto contenido',),
        }

class product_descripcion(osv.osv):
	_name = 'product.descripcion'
	_columns = {
		'product_id': fields.many2one('product.product',string="Producto", required=True,),
		'name': fields.char('Descripcion'),
		'fecha': fields.date('Fecha'),
		'sale_order_ids': fields.one2many('sale.order.line','descripcion_sale_id',string='Lineas de Ventas'),
	}
	_defaults = {
		'fecha': lambda *a: time.strftime('%Y-%m-%d'),
	}

class sale_order_line(osv.osv):
	_name='sale.order.line'
	_inherit = 'sale.order.line'
	_columns = {
                'descripcion_sale_id': fields.many2one('product.descripcion', string="Descripciones"),
	}
	
	def descripcion_sale_change(self,cr,uid,ids,descripcion_sale_id,product_id,name='',context=None):
		res = {}
		if descripcion_sale_id:
			prod = self.pool.get('product.descripcion').name_get(cr,uid,descripcion_sale_id,context=context)[0][1]
			return {'value': {'name': prod}}
		return {}


