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


from openerp.report import report_sxw
import time
import netsvc
from datetime import  datetime
from dateutil.relativedelta import relativedelta
import pytz
import logging

logger = logging.getLogger(__name__)

#from openerp.osv import fields, osv, orm
#from openerp import tools

class product_kardex_report(report_sxw.rml_parse):

    def _get_move_details(self, form):
        res = {}
        data = []
        move_qty_saldo = 0.0
        move_qty_saldo_ini = 0.0

        move_qty_total_out = 0.0
        move_qty_total_in = 0.0
        s_saldo_inicial = 0.0 #Variabale temporal

        stock_move_obj = self.pool.get('stock.move')

        sale_obj = self.pool.get('sale.order')
        invoice_obj = self.pool.get('account.invoice')
        purchase_obj = self.pool.get('purchase.order')

        prod_id = form['product_ids'] # muestra una tupla (1,JAVIER SALAZAR CARLOS)
        locat_id = form['location_ids']
        date_start = form['fecha_desde']
        date_end = form['fecha_hasta']
        
        fecha_utc_desde = (datetime.strptime(date_start + ' 00:00:00', '%Y-%m-%d %H:%M:%S') + relativedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S") 
        move_ids_desde = stock_move_obj.search(self.cr,self.uid,[('date','<',fecha_utc_desde),('product_id','=',prod_id[0]),('state','=','done'),'|',('location_id','=',locat_id[0]),('location_dest_id','=',locat_id[0])], order='date') 
        for move_desde in stock_move_obj.browse(self.cr, self.uid, move_ids_desde):

            if move_desde.location_id.id != locat_id[0] and move_desde.location_dest_id.id == locat_id[0]:
                move_qty_saldo_ini = move_qty_saldo_ini + move_desde.product_qty
                move_qty_saldo = move_qty_saldo_ini
            if move_desde.location_id.id == locat_id[0] and move_desde.location_dest_id.id != locat_id[0]:
                move_qty_saldo_ini = move_qty_saldo_ini - move_desde.product_qty
                move_qty_saldo = move_qty_saldo_ini
            
        s_saldo_inicial = move_qty_saldo    #para hacer entre como saldo inicial y sume
        move_qty_total_in = s_saldo_inicial # 
        #Imprime si hay saldo inicial
        if  move_ids_desde: 
            res.update({'concept_move': 'SALDO INICIAL' }) 
            res.update({'product_qty_in': move_qty_saldo })            
            res.update({'move_saldo': move_qty_saldo})
            data.append(res)
        #fin imprime

        fecha_utc_hasta = (datetime.strptime(date_end + ' 23:59:59', '%Y-%m-%d %H:%M:%S') + relativedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S") 
        move_ids_hasta = stock_move_obj.search(self.cr,self.uid,[ ('date','>=',fecha_utc_desde) ,('date','<=',fecha_utc_hasta),('product_id','=',prod_id[0]),('state','=','done'),'|',('location_id','=',locat_id[0]),('location_dest_id','=',locat_id[0])], order='date') # Obtenemos el id
        
        for move in stock_move_obj.browse(self.cr, self.uid, move_ids_hasta):
            res = {
                    'produ_name': move.product_id.name,
                    'date': move.date,
                    'n_guia': move.picking_id.name,
                        }
 
            if move.origin:
                if move.picking_id.type in ('out'):
                    sale_order_id = sale_obj.search(self.cr,self.uid,[('name','=',move.origin)]) # Obtenemos el id
                    for sale in sale_obj.browse(self.cr, self.uid, sale_order_id):
                        account_invoice_id  = invoice_obj.search(self.cr,self.uid,[('origin','=',sale.name)]) # Obtenemos el id
                        if account_invoice_id:
                            for invoice in invoice_obj.browse(self.cr, self.uid, account_invoice_id):
                                res.update({'n_fact': invoice.number or ''})
                if move.picking_id.type in ('in'):
                    purchase_order_id = purchase_obj.search(self.cr,self.uid,[('name','=',move.origin)]) # Obtenemos el id
                    for purchase in purchase_obj.browse(self.cr, self.uid, purchase_order_id):
                        account_invoice_id  = invoice_obj.search(self.cr,self.uid,[('origin','ilike',purchase.name)]) # Obtenemos el id
                        if account_invoice_id:
                            for invoice in invoice_obj.browse(self.cr, self.uid, account_invoice_id):
                                res.update({'n_fact': invoice.number or '' })
            #para ver si es un movimiento de composicion
            if move.make_move_id:
                res.update({'n_guia': move.make_move_id.name })

            #para ver si es un movimiento de ajuste de inventario
            if move.ajuste_move_id:
                res.update({'n_guia': move.ajuste_move_id.name })

            if move.location_id.id != locat_id[0] and move.location_dest_id.id == locat_id[0]:
                move_qty_saldo = move_qty_saldo + move.product_qty
                move_qty_total_in = move_qty_total_in + move.product_qty #suma vertical
                #logger.error("INNNNNN: %r", move_qty_total_in)

                res.update({'product_qty_in': move.product_qty })
                res.update({'move_saldo': move_qty_saldo })
                res.update({'product_qty_out': 0.0 })

                if move.location_id.usage == 'supplier' and move.location_dest_id.usage == 'internal':
                    res.update({'concept_move': 'COMPRAS DE PRODUCTO' })
                if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'customer':
                    res.update({'concept_move': 'VENTAS DE PRODUCTO' })
                #Ajuste de inventario
                if move.location_id.usage == 'inventory' and move.location_dest_id.usage == 'internal':
                    res.update({'concept_move': 'AJUSTE DE INVENTARIO (INGRESO)' })
                if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'inventory':
                    res.update({'concept_move': 'AJUSTE DE INVENTARIO (EGRESO)' })
                #Produccion de productos
                if move.location_id.usage == 'production' and move.location_dest_id.usage == 'internal':
                    res.update({'concept_move': 'PRODUCCION' })
                if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'production':
                    res.update({'concept_move': 'CONSUMO PARA PRODUCCION' })
                #Composicion de productos
                if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'composition':
                    res.update({'concept_move': 'COMPOSICION DE PRODUCTOS' })
                if move.location_id.usage == 'composition' and move.location_dest_id.usage == 'internal':
                    res.update({'concept_move': 'COMPOSICION DE PRODUCTOS' })
                #AJUSTE DE INVENTARIO
                if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'ajuste':
                    res.update({'concept_move': 'SALIDA POR AJUSTE DE INVENTARIO' })
                if move.location_id.usage == 'ajuste' and move.location_dest_id.usage == 'internal':
                    res.update({'concept_move': 'INGRESO POR AJUSTE DE INVENTARIO' })

                if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'internal':
                    res.update({'concept_move': 'TRANFERENCIA ENTRE ALMACENES' })
                if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'transit':
                    res.update({'concept_move': 'TRANFERENCIA ENTRE ALMACENES' })
                if move.location_id.usage == 'transit' and move.location_dest_id.usage == 'internal':
                    res.update({'concept_move': 'TRANFERENCIA ENTRE ALMACENES' })
                if move.location_id.usage == 'customer' and move.location_dest_id.usage == 'internal':
                    res.update({'concept_move': 'DEVOLUCION DE PRODUCTOS' })
                #recepcion de muestra
                if move.location_id.usage == 'muestra' and move.location_dest_id.usage == 'internal':
                    res.update({'concept_move': 'DEVOLUCION DE PRODUCTOS MUESTRA' })
                #data.append(res)

            if move.location_id.id == locat_id[0] and move.location_dest_id.id != locat_id[0]:
                move_qty_saldo = move_qty_saldo - move.product_qty
                move_qty_total_out = move_qty_total_out + move.product_qty # suma vertical

                res.update({'product_qty_out': move.product_qty})
                res.update({'move_saldo': move_qty_saldo})
                res.update({'product_qty_in': 0.0})

                if move.location_id.usage == 'supplier' and move.location_dest_id.usage == 'internal':
                    res.update({'concept_move': 'COMPRAS DE PRODUCTO' })
                if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'customer':
                   	res.update({'concept_move': 'VENTAS DE PRODUCTO' })
                #Ajuste de inventario
                if move.location_id.usage == 'inventory' and move.location_dest_id.usage == 'internal':
                    res.update({'concept_move': 'AJUSTE DE INVENTARIO' })
                if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'inventory':
                    res.update({'concept_move': 'AJUSTE DE INVENTARIO' })
                #Produccion de productos
                if move.location_id.usage == 'production' and move.location_dest_id.usage == 'internal':
                    res.update({'concept_move': 'PRODUCIDO(S)' })
                if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'production':
                    res.update({'concept_move': 'CONSUMO PARA PRODUCCION' })
                #Composicion de productos
                if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'composition':
                    res.update({'concept_move': 'COMPOSICION DE PRODUCTOS' })
                if move.location_id.usage == 'composition' and move.location_dest_id.usage == 'internal':
                    res.update({'concept_move': 'DESCOMPOSICION DE PRODUCTOS' })

                #AJUSTE DE INVENTARIO
                if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'ajuste':
                    res.update({'concept_move': 'SALIDA POR AJUSTE DE INVENTARIO' })
                if move.location_id.usage == 'ajuste' and move.location_dest_id.usage == 'internal':
                    res.update({'concept_move': 'INGRESO POR AJUSTE DE INVENTARIO' })

                if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'internal':
                    res.update({'concept_move': 'TRANFERENCIA ENTRE ALMACENES' })
                if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'transit':
                    res.update({'concept_move': 'TRANFERENCIA ENTRE ALMACENES' })
                if move.location_id.usage == 'transit' and move.location_dest_id.usage == 'internal':
                    res.update({'concept_move': 'TRANFERENCIA ENTRE ALMACENES' })
                    
                if move.location_id.usage == 'customer' and move.location_dest_id.usage == 'internal':
                    res.update({'concept_move': 'DEVOLUCION DE PRODUCTOS (INGRESO)' })
                # envio a muestra
                if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'muestra':
                    res.update({'concept_move': 'ENVIO DE PRODUCTOS A MUESTRA' })

                #data.append(res)
            res.update({'move_qty_total_in': move_qty_total_in})
            res.update({'move_qty_total_out': move_qty_total_out})
            data.append(res)

        return data

    def _get_name_location(self, form):
        res = {}
        data = []
        location_obj = self.pool.get('stock.location')
        locat_ids = location_obj.search(self.cr,self.uid,[('id','=',form['location_ids'][0])]) # Obtenemos el id
        for locat in location_obj.browse(self.cr, self.uid, locat_ids):
            res = {'location_name': locat.name }
            data.append(res)
        return data
    def _get_name_product(self,form):
        res = {}
        data = []
        product_obj = self.pool.get('product.product')
        product_ids = product_obj.search(self.cr,self.uid,[('id','=',form['product_ids'][0])]) # Obtenemos el id
        for produ in product_obj.browse(self.cr, self.uid, product_ids):
            res = {'product_name': produ.name }
            data.append(res)
        return data

    def __init__(self, cr, uid, name, context):
        super(product_kardex_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
                        'time': time,
                        'get_move_details': self._get_move_details,
                        'get_name_product' : self._get_name_product,
                        'get_name_location': self._get_name_location,               
        })


report_sxw.report_sxw('report.kardex.product','stock.move', 'addons/product_kardex/report/product_kardex_report.rml',parser=product_kardex_report,header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
