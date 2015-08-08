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

from osv import osv, fields, orm
import base64 
import time
from tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class sunat_detraccion_adquiriente(osv.osv):
    _name = 'sunat.detraccion.adquiriente'

    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            #res[order.id] = {'i_total': 0}
            val = 0
            for line in order.proveedores_ids:
                val+= line.importe            
            res[order.id] = val
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if 'ruc_adquiriente' in vals and 'n_lote' in vals:       
            vals.update({'name': 'D'+vals['ruc_adquiriente']+ vals['n_lote'] })  
            #_logger.error("WUIRTE: %r", vals)            
            return super(sunat_detraccion_adquiriente, self).write(cr, uid, ids, vals, context=context)
        elif 'ruc_adquiriente' in vals and 'n_lote' not in vals:
            for value in self.browse(cr, uid, ids, context=context):
                n_lote = value.n_lote
                vals.update({'name': 'D'+vals['ruc_adquiriente']+ n_lote })
            return super(sunat_detraccion_adquiriente, self).write(cr, uid, ids, vals, context=context)
        elif 'ruc_adquiriente' not in vals and 'n_lote' in vals:
            for value in self.browse(cr, uid, ids, context=context):
                ruc = value.ruc_adquiriente
                vals.update({'name': 'D'+ruc+ vals['n_lote'] })
            return super(sunat_detraccion_adquiriente, self).write(cr, uid, ids, vals, context=context)
        else:
            return super(sunat_detraccion_adquiriente, self).write(cr, uid, ids, vals, context=context)


    _columns = {
        'name':fields.char('Nombre', size=18),
        'state': fields.selection(
          [('draft','Borrador'),('done','Pagado'),('cancel','Anulado')],'Estado',readonly=True,required=True
        ),
        'ruc_adquiriente': fields.char('Ruc adquiriente', size=11, required=True, states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
        'n_adquiriente': fields.many2one('res.partner','Nombre/Razon Social',ondelete='cascade',required=True,states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
        #'anio': fields.char('anio',size=4,required=True,),
        'anio': fields.selection([('2015','2015'),('2014','2014'),('2013','2013')],'Anio',required=True, states={'done':[('readonly',True)], 'cancel':[('readonly',True)]} ),
        'n_correlativo': fields.char('Numero correlativo',size=4,required=True, states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
        'n_lote': fields.char('Numero de lote',size=6, states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),      
        #'i_total': fields.char('Importe total',size=15),
        'i_total':  fields.function(_amount_all,type="integer", method=True, string="Importe total", states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
        'fecha': fields.datetime(string='Fecha', states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
        'proveedores_ids': fields.one2many('sunat.detraccion.adquiriente.proveedor','adquiriente_id',string="Nuevo proveedor", states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
        'txt_filename': fields.char(''),
        'txt_binary': fields.binary()
        }
    _order='fecha desc'    
    _defaults = {
        'fecha': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'name': lambda obj, cr, uid, context: '/',
        'state': 'draft',
   		}
    def onchange_ruc(self, cr, uid, ids, ruc_adquiriente, context=None):
        if context is None:
            context = {}
        value = {}
        partner_obj = self.pool.get('res.partner')
        if ruc_adquiriente:
            partner_id = partner_obj.search(cr,uid,[('doc_number','=',ruc_adquiriente)])
            if partner_id:
                value.update({
                       'n_adquiriente': partner_id,
                    })
                return {'value': value}
            else:
                raise osv.except_osv(_('Warning!'), _('Empresa no registrado en el sistema.'))
        else:            
            return {'value': {'n_adquiriente': False, 'ruc_adquiriente': False}}

    def onchange_n_adquiriente(self, cr, uid, ids, n_adquiriente, context=None):
        value = {}
        if not n_adquiriente:
            return {'value': {'n_adquiriente': False, 'ruc_adquiriente': False}}
        
        adquiriente = self.pool.get('res.partner').browse(cr, uid, n_adquiriente, context=context)
        value.update({
               'ruc_adquiriente': adquiriente.doc_number,
            })
        return {'value': value}

    def onchange_n_lote(self, cr, uid, ids, anio, n_correlativo, context=None):
        res = {'value':{}}
        res['value']['n_lote'] = (anio and (anio[2:]) or '') + (n_correlativo and (n_correlativo) or '')
        return res
    
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        detraccion_id = super(sunat_detraccion_adquiriente, self).create(cr, uid, vals,context=context)

        if detraccion_id:
            ruc = self.browse(cr, uid, detraccion_id, context).ruc_adquiriente
            n_lote = self.browse(cr, uid, detraccion_id, context).n_lote
            vals = {'name': 'D'+ruc+n_lote }
        self.write(cr, uid, detraccion_id, vals, context=context)
        return detraccion_id
    
    def generate_file(self, cr, uid, ids, context=None):
        """
        function called from button
        """
        name_save =  None
        formato = ""
        formato1 = ""
        list_result = []
        list_result1 = []
        for value in self.browse(cr, uid, ids):
            name_save = value.name
            ind_maestra = '*'
            ruc = value.ruc_adquiriente

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

            formato = str("%s%s%s%s%s\r\n"%(ind_maestra,ruc,nuevo_name,lote,nuevo_total))

            for line in value.proveedores_ids:
                tipo_doc = line.tipo_doc
                ruc_prove = line.ruc_proveedor
                name_proveedor = '                                   '
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
                formato1 += str("%s%s%s%s%s%s%s%s%s%s%s%s\r\n"%(tipo_doc,ruc_prove,name_proveedor,n_proforma,codigo_bien_servic,n_banco_provee,nuevo_importe,tipo_operac,period_tribu,tipo_comprob,serie_comprob,numer_comprob))

        #_logger.error("MI VALOR 4: %r", formato1[:-2])
        return self.write(cr, uid, ids, {
            'txt_filename': name_save+'.txt',
            'txt_binary': base64.encodestring(formato + formato1[:-2])
        }, context=context)    

    def button_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, { 'state' : 'done' })
        return True      
    def button_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, { 'state' : 'cancel' })
        return True  
    #Evita eliminar  cuando esta en estado pagado.
    def unlink(self, cr, uid, ids, context=None):
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.state == 'draft' or rec.state == 'done' :
                raise osv.except_osv(_('ERROR!'), _('No se puede eliminar, debe de anular primero!'))
        return super(sunat_detraccion_adquiriente, self).unlink(cr, uid, ids, context=context)             

class sunat_detraccion_adquiriente_proveedor(osv.osv):
    _name = 'sunat.detraccion.adquiriente.proveedor'
    _columns = {
    	'name':fields.many2one('res.partner','Nombre/Razon Social', ondelete='cascade',required=True),
        'ruc_proveedor': fields.char('Ruc proveedor',size=11, required=True),
        'nro_proforma': fields.char('Numero de proforma',size=9, ),
        'tipo_doc': fields.selection([
            ('1','1-DNI'),
            ('4','4-Carnet de extranajeria'),
            ('6','6-RUC'),
            ('7','7-Pasaporte'),
            ('8','8-Pasaporte'),
            ('A','A-Cedula Diplomatica de Identidad '),
            ],'Tipo de Documeto proveedor',required=True,),
        'n_cuenta': fields.char('Numero de cuenta',size=11, required=True),        
        'tipo_bien_servicio': fields.selection([
            ('001','001-Azucar'),
            ('002','002-Arroz Pilado'),
            ('003','003-Alcohol etilico'),
            ('004','004-Recursos hidrobiologicos'),
            ('005','005-Maiz amarillo duro'),
            ('006','006-Algodon'),
            ('007','007-Cania de azucar'),
            ('008','008-Madera'),
            ('009','009-Arena y piedra'),
            ('010','010-Residuos, subproductos,desechos, recortes y desperdicios y formas primarias derivadas de los mismos (1)'),
            ('011','011-Bienes gravados con el IGV, por renuncia a la exoneración (2)'),
            ('012','012-Intermediacion laboral y tercerizacion'),
            ('013','013-Animales vivos '),
            ('014','014-Carnes y despojos comestibles'),
            ('015','015-Abonos, cueros y pieles de origen animal'),
            ('016','016-Aceite de pescado'),
            ('017','017-Harina, polvo y pellets de pescado, crustaceos, moluscos y demas invertebrados acuaticos'),
            ('018','018-Embarcaciones pesqueras'),
            ('019','019-Arrendamiento de bienes muebles'),
            ('020','020-Mantenimiento y reparación de bienes muebles'),
            ('021','021-Movimiento de carga'),
            ('022','022-Otros servicios empresariales'),
            ('023','023-Leche'),
            ('024','024-Comision mercantil'),
            ('025','025-Fabricacion de bienes por encargo'),
            ('026','026-Servicio de transporte de personas'),
            ('027','027-Servicio de transporte de bienes realizado por via terrestre'),
            #('028','028-Servicio de transporte publico de pasajeros realizado por via terrestre'),
            ('029','029-Algodón  en rama  sin desmotar'),
            ('030','030-Contratos de construccion'),
            ('031','031-Oro gravado con el IGV (2)'),
            ('032','032-Paprika y otros frutos de los géneros capsicum o pimienta'),
            ('033','033-Esparragos'),
            ('034','034-Minerales metalicos no auriferos'),
            ('035','035-Bienes exonerados del IGV (3)'),
            ('036','036-Oro y demás minerales metálicos exonerados del IGV (3)'),
            ('037','037-Demas servicios gravados con el IGV'),
            ('038','038-Espectáculos públicos no deportivos (4)'),
            ('039','039-Minerales no metálicos (3)'),
            ('040','040-Bien inmueble gravado con el IGV  (5)'),
            ('041','041-Plomo (6)'),
            ], 'Tipo de bien o servicio',required=True,),
        'tipo_operacion': fields.selection([
            ('01','01-Venta de bienes muebles o inmuebles, prestación de servicios o contratos de construcción gravados con el IGV'),
            ('02','02-Retiro de bienes gravados con el IGV'),
            ('03','03-Traslado de bienes fuera del centro de producción, así como desde cualquier zona geográfica que goce de beneficios tributarios hacia el resto del país, cuando dicho traslado no se origine en una operación de venta.'),
            ('04','04-Venta de bienes gravada con el IGV realizada a través de la Bolsa de Productos.'),
            ('05','05-Venta de bienes exonerada del IGV'),
            ],'Tipo de Operacion',required=True,),
        #'importe': fields.char('Importe del deposito',size=15),
        #'importe': fields.float('Importe',digits=(2,1)), 
        'importe': fields.integer('Importe',required=True),
        'p_tributario': fields.char('Periodo Tributario',size=6,required=True),
        #'p_tributario': fields.selection([('2015','2015'),('2014','2014'),('2013','2013')],'Periodo Tributario',readonly=True,required=True ),
        'tipo_comprobante': fields.selection([
            ('01','01-Factura'),
            ('03','03-Boleta'),
            ('09','09-Guia remision - remitente'),
            ],'Tipo de Comprobante',required=True,),
       	's_comprobante': fields.char('Serie comprobante',size=4, required=True),
       	'n_comprobante': fields.char('Numero comprobante',size=8, required=True),
       	'adquiriente_id':fields.many2one('sunat.detraccion.adquiriente','Adquiriente',ondelete='cascade',required=True),

        }
    _defaults = {
        'tipo_doc': '6',
   		}

    def onchange_ruc(self, cr, uid, ids, ruc_proveedor, context=None):
        if context is None:
            context = {}
        value = {}
        partner_obj = self.pool.get('res.partner')
        if ruc_proveedor:
            partner_id = partner_obj.search(cr,uid,[('doc_number','=',ruc_proveedor)])
            if partner_id:                
                value.update({'name': partner_id,})
                return {'value': value}
            else:
                raise osv.except_osv(_('Warning!'), _('Empresa no registrado en el sistema.'))
        else:            
            return {'value': {'name': False, 'ruc_proveedor': False,'n_cuenta': False}}

    def onchange_name(self, cr, uid, ids, name, context=None):
        value = {}
        if not name:
            return {'value': {'ruc_proveedor': False, 'name': False,'n_cuenta': False}}

        proveedor = self.pool.get('res.partner').browse(cr, uid, name, context=context)
        bank = None
        for line in proveedor.bank_ids:
            bank = line.acc_number
            #_logger.error("MI BANCO: %r", )
        value.update({'ruc_proveedor': proveedor.doc_number,'n_cuenta':bank,})
        return {'value': value}



class sunat_detraccion_proveedor(osv.osv):
    _name ='sunat.detraccion.proveedor'
    _columns = {
        #'recep_compras': fields.boolean('Recepcion de compras',help="Permite que este almacen se recepcione productos de compra"), 
    }

 
