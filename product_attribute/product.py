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
        'procedencia': fields.selection([('nac','Nacional'),('import','Importado')],'Procedencia',required=False,),
        'categ_edad': fields.selection([('01','0 A 5 MESES'),('02','6 A 11 MESES'),('03','1 AÑO'),('04','2 AÑOS'),('05','3 AÑOS'),('06','4 Y 5 AÑOS'),],'Categoria Edad',required=False,),
        'categ_area': fields.selection([('01','AREA COGNITIVA'),('02','AREA DE LENGUAJE'),('03','AREA DE MOTORA GRUESA'),('04','AREA DE MOTORA FINA'),('05','AREA SOCIO-EMOCIONAL'),],'Categoria Area',required=False,),
	}