# -*- encoding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (c) 2015 SC. (http://salazarcarlos.com).
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

#import time,dateutil, dateutil.tz
#from dateutil.relativedelta import relativedelta

#from datetime import date, datetime

import logging
_logger = logging.getLogger(__name__)

class product_kardex_wizard(osv.osv_memory):
    _name = 'sunat.adquiriente.proveedor.wizard'
    #_description = 'Imprime el kardex de un producto'

    _columns = {
        'detraccion_ids': fields.many2one('sunat.detraccion.adquiriente', 'Detraccion', required="True"),
    }

    def print_txt(self, cr, uid, ids, context=None):
        datas = {}

        if context is None:
            context = {}

        #datas = {'ids': context.get('active_ids', [])} #
        res = self.read(cr, uid, ids, ['detraccion_ids'], context=context)
        dtr_id=None
        for val in res:
            dtr_id = val['detraccion_ids'] #OBTENEMOS EL ID
            #_logger.error("MI VALOR 1: %r", dtr_id[0])

        sunat_adqui_provee_obj = self.pool.get('sunat.detraccion.adquiriente')
        t_id = sunat_adqui_provee_obj.search( cr, uid,[('id','=', dtr_id[0] )])
        
        name_save =  None
        formato = ""
        formato1 = ""
        list_result = []
        list_result1 = []

        for value in sunat_adqui_provee_obj.browse(cr, uid, t_id, context=context):
            name_save = value.name
            ind_maestra = '*'
            ruc=value.ruc_adquiriente
            #partner = self.pool.get('res.partner').browse(cr, uid, value.n_adquiriente.id, context=context)
            
            name= value.n_adquiriente.name
            #COMPLETAR CON CEROS AL NOMBRE
            nuevo_name = None
            if len(name) < 35:
                indice = 1
                nuevo_name = name
                while indice <= 35 - len(name) :
                    nuevo_name =  nuevo_name + ' '
                    indice += 1 
            elif len(name) == 35:
                nuevo_name = name
            else:
                nuevo_name = name[:35]

            lote = value.n_lote

            total = str(value.i_total)
            #COMPLETAR CON CEROS AL MONTO
            nuevo_total = None
            if len(total) < 13:
                indice = 1
                nuevo_total = total
                while indice <= 13 - len(total) :
                    nuevo_total = '0' + nuevo_total
                    indice += 1
                nuevo_total = nuevo_total + '00' 
                #_logger.error("MI VALOR 4: %r", nuevo_total)
            else:
                nuevo_total =  total                

            formato = str("%s%s%s%s%s"%(ind_maestra,ruc,nuevo_name,lote,nuevo_total))
            list_result.append(formato) 

        for value in sunat_adqui_provee_obj.browse(cr, uid, t_id, context=context):
            for line in value.proveedores_ids:
                tipo_doc = line.tipo_doc
                ruc_prove = line.ruc_proveedor
                n_proforma = '000000000'
                codigo_bien_servic = line.tipo_bien_servicio
                n_banco_provee = line.n_cuenta

                impor_deposit = str(line.importe)
                nuevo_importe = None
                if len(impor_deposit) < 13:
                    indice = 1
                    nuevo_importe = impor_deposit
                    while indice <= 13 - len(impor_deposit) :
                        nuevo_importe = '0' + nuevo_importe
                        indice += 1 
                    nuevo_importe = nuevo_importe + '00'
                tipo_operac = line.tipo_operacion
                period_tribu = line.p_tributario
                tipo_comprob = line.tipo_comprobante
                serie_comprob = line.s_comprobante
                numer_comprob = line.n_comprobante
                formato1 = str("%s%s%s%s%s%s%s%s%s%s%s"%(tipo_doc,ruc_prove,n_proforma,codigo_bien_servic,n_banco_provee,nuevo_importe,tipo_operac,period_tribu,tipo_comprob,serie_comprob,numer_comprob))
                list_result1.append(formato1)

            #list_result.append(formato)
            #_logger.error("MI VALOR 3: %r", name)

        #generara el reporte en formato *.txt
        #datas = {'ids': context.get('active_ids', [])}       
        datas['form_cb'] = {'list_result': list_result} 
        datas['form_cp'] = {'list_result1': list_result1}  
        #_logger.error("DTASSSSS1: %r", datas)
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'sunat_detraccion',
            'datas': datas,
            'report_type': 'txt',
        }



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: