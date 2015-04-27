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
        'type_existence': fields.selection([
            ('01','MERCADERIAS'),
            ('02','PRODUCTOS TERMINADOS'),
            ('03','MATERIAS PRIMAS'),
            ('04','ENVASES'),
            ('05','MATERIALES AUXILIARES'),
            ('06','SUMINISTROS'),
            ('07','REPUESTOS'),
            ('08','EMBALAJES'),
            ('09','SUBPRODUCTOS'),
            ('10','DESECHOS Y DESPERDICIOS'),
            ('91','OTROS 1'),
            ('92','OTROS 2'),
            ('93','OTROS 3'),
            ('94','OTROS 4'),
            ('95','OTROS 5'),
            ('96','OTROS 6'),
            ('97','OTROS 7'),
            ('98','OTROS 8'),
            ('99','OTROS 9'),
            ],
            'Tipo de existencia',required=False,),
        'cod_producto': fields.char('Codigo Producto')
    }
