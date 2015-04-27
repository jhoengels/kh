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

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time

from osv import osv, fields,orm
import netsvc
from tools.translate import _
import decimal_precision as dp

class stock_picking_in(osv.osv):
    _inherit = "stock.picking.in"
    _columns = {
        'guia_supplier': fields.char('Nro Guia Proveedor', size=64),
        'fact_supplier': fields.char('Nro Factura Proveedor', size=64),
        }

class stock_picking(osv.osv):
    _inherit = "stock.picking"
    _columns = {
        'guia_supplier': fields.char('Nro Guia Proveedor', size=64),
        'fact_supplier': fields.char('Nro Factura Proveedor', size=64),
        'bultos': fields.integer('Bultos'),
        'peso': fields.float('Peso',digits=(2,1)),
        }

class stock_picking_out(osv.osv):
    _inherit = "stock.picking.out"
    _columns = {
        'bultos': fields.integer('Bultos'),
        'peso': fields.float('Peso',digits=(2,1)),
        }

 
