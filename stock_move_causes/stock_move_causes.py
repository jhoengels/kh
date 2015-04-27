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

from openerp.osv import osv,fields,orm
from openerp import netsvc
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class stock_move_causes(osv.osv):
    _name = 'stock.move.causes'
    _columns = {
        'name': fields.char('Nombre', size=64),
        'active': fields.boolean('Active', help="Para no visualizar desactivarlo"),
        'subcauses_ids': fields.one2many('stock.move.subcauses','cause_id',string="Nueva subcausa"),
       }
    _defaults = {
        'active': 1,
        }

class stock_move_subcauses(osv.osv):
    _name = 'stock.move.subcauses'
    _columns = {
        'name': fields.char('Nombre', size=64),
        'active': fields.boolean('Active', help="Para no visualizar desactivarlo"),
        'cause_id':fields.many2one('stock.move.causes','Causa',ondelete='cascade',required=True),
       } 
    _defaults = {
        'active': 1,
         }

class stock_move(orm.Model):
    _inherit = 'stock.move'

    _columns = {
        'cause_id':fields.many2one('stock.move.causes','Causa',required=False),
        'subcause_id':fields.many2one('stock.move.subcauses','SubCausa',required=False),
        }

    def onchange_causes(self, cr, uid, ids, cause_id, context=None):
        value = {}
        value['subcause_id'] = False
        return {'value': value}


class stock_picking_out(orm.Model):
    _inherit = "stock.picking.out"
 
    _columns = {
        'cause_id':fields.many2one('stock.move.causes','Causa', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'subcause_id':fields.many2one('stock.move.subcauses','SubCausa', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        }

    def onchange_causes(self, cr, uid, ids, cause_id, context=None):
        value = {}
        value['subcause_id'] = False
        return {'value': value}


class stock_picking_in(orm.Model):
    _inherit = "stock.picking.in"
 
    _columns = {
        'cause_id':fields.many2one('stock.move.causes','Causa', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'subcause_id':fields.many2one('stock.move.subcauses','SubCausa', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        }

    def onchange_causes(self, cr, uid, ids, cause_id, context=None):
        value = {}
        value['subcause_id'] = False
        return {'value': value}

class stock_picking(orm.Model):
    _inherit = 'stock.picking'
    _columns = {
        'cause_id':fields.many2one('stock.move.causes','Causa', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'subcause_id':fields.many2one('stock.move.subcauses','SubCausa', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        }

    def onchange_causes(self, cr, uid, ids, cause_id, context=None):
        value = {}
        value['subcause_id'] = False
        return {'value': value}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: