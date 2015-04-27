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


class stock_transportista(osv.osv):
    _name = 'stock.transportista'
    _columns = {
        'name': fields.char('Nombre', size=64),
        'ruc': fields.char('RUC', size=32),
        'sede_ids': fields.one2many('stock.transportista.sede','transportista_id',string="Nueva Sede"),
        'conductor_ids': fields.one2many('stock.transportista.conductor','transportista_id',string="Nueva conductor"),
        'carro_ids': fields.one2many('stock.transportista.carro','transportista_id',string="Nueva carro"),
        'active': fields.boolean('Active', help="Para no visualizar desactivarlo"),

    }

    _defaults = {
        'active': 1,
        }

class stock_transportista_sede(osv.osv):
    _name = 'stock.transportista.sede'
    _columns = {
        #'name': fields.char('Nombre', size=64),
        'name': fields.char('Direccion', size=64),
        'state_id': fields.many2one("res.country.state", 'Departamento/Provincia/Distrito', ondelete='cascade', select=True,),
        'transportista_id':fields.many2one('stock.transportista','Empresa',ondelete='cascade', select=True,),
        'active': fields.boolean('Active', help="Para no visualizar desactivarlo"),

       } 
    _defaults = {
        'active': 1,
         }

    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
	    if view_type == 'form' and not view_id:
	        mod_obj = self.pool.get('ir.model.data')
	        #if self._name == "stock.picking.in":
	        model, view_id = mod_obj.get_object_reference(cr, uid, 'delivery_extension', 'view_stock_transportista_sede_form')
	        #if self._name == "stock.picking.out":
	        #    model, view_id = mod_obj.get_object_reference(cr, uid, 'stock', 'view_picking_out_form')
	    return super(stock_transportista_sede, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)


class stock_transportista_conductor(osv.osv):
    _name = 'stock.transportista.conductor'
    _columns = {
        'name': fields.char('Apellidos y Nombres', size=64),
        'licencia': fields.char('Licencia', size=32),
        'active': fields.boolean('Active', help="Para no visualizar desactivarlo"),
        'transportista_id':fields.many2one('stock.transportista','Empresa',ondelete='cascade', select=True),
        #'carro_ids': fields.one2many('stock.transportista.conductor','transportista_id',string="Nueva carro"),
       } 
    _defaults = {
        'active': 1,
         }

class stock_transportista_carro(osv.osv):
    _name = 'stock.transportista.carro'
    _columns = {
        'name': fields.char('Placa', size=64),
		'marca': fields.char('Marca', size=32),
        'active': fields.boolean('Active', help="Para no visualizar desactivarlo"),
        'transportista_id':fields.many2one('stock.transportista','Empresa',ondelete='cascade', select=True),
        #'conductor_id':fields.many2one('stock.transportista.conductor','Conductor',ondelete='cascade',),
       } 
    _defaults = {
        'active': 1,
         }


class stock_picking(orm.Model):
    _inherit = 'stock.picking'
    _columns = {
        'transportista_id':fields.many2one('stock.transportista','Empresa', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'partida_id':fields.many2one('stock.transportista.sede','Punto partida', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'conductor_id':fields.many2one('stock.transportista.conductor','Conductor', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'carro_id':fields.many2one('stock.transportista.carro','Placa/Marca', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'llegada_id':fields.many2one('stock.transportista.sede','Punto llegada sucursal', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'llegadacliente_id':fields.many2one('res.partner','Punto llegada cliente', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),

        'transportista2_id':fields.many2one('stock.transportista','Empresa', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'partida2_id':fields.many2one('stock.transportista.sede','Punto partida agencia', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'conductor2_id':fields.many2one('stock.transportista.conductor','Conductor', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'carro2_id':fields.many2one('stock.transportista.carro','Placa/Marca', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'llegada2_id':fields.many2one('stock.transportista.sede','Punto llegada agencia', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'llegadacliente2_id':fields.many2one('res.partner','Punto llegada cliente', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),       
    }


class stock_picking_out(orm.Model):
    _inherit = "stock.picking.out"
    _columns = {
        'transportista_id':fields.many2one('stock.transportista','Empresa', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'partida_id':fields.many2one('stock.transportista.sede','Punto partida', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'conductor_id':fields.many2one('stock.transportista.conductor','Conductor', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'carro_id':fields.many2one('stock.transportista.carro','Placa/Marca', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'llegada_id':fields.many2one('stock.transportista.sede','Punto llegada agencia', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'llegadacliente_id':fields.many2one('res.partner','Punto llegada cliente', help="Direccion a donde se entregara la mercaderia, dejar vacio si se lleva a alguna agencia de transporte", states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),


        'transportista2_id':fields.many2one('stock.transportista','Empresa', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'partida2_id':fields.many2one('stock.transportista.sede','Punto partida agencia', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'conductor2_id':fields.many2one('stock.transportista.conductor','Conductor', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'carro2_id':fields.many2one('stock.transportista.carro','Placa/Marca', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'llegada2_id':fields.many2one('stock.transportista.sede','Punto llegada agencia', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}), 
        'llegadacliente2_id':fields.many2one('res.partner','Punto llegada cliente', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),       
    }

    def onchange_llegadacliente(self, cr, uid, ids, llegadacliente_id, transportista2_id, context=None):
        value = {}
        
        value['transportista2_id'] = False
        value['partida2_id'] = False
        value['carro2_id'] = False
        value['llegada2_id'] = False
        value['llegadacliente2_id'] = False
        return {'value': value}

    def onchange_transportista2(self, cr, uid, ids, transportista2_id, llegadacliente_id, context=None):
        value = {}
        
        value['llegadacliente_id'] = False
        value['partida2_id'] = False
        value['carro2_id'] = False
        value['llegada2_id'] = False
        value['llegadacliente2_id'] = False
        return {'value': value}

