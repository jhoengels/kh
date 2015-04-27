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


import time
from report import report_sxw
import logging
_logger = logging.getLogger(__name__)

name_text= None
class sunat_detraccion_adquiriente_txt(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(sunat_detraccion_adquiriente_txt, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_detalle_cabecera': self.get_detalle_cabecera,
            'get_detalle_cuerpo': self.get_detalle_cuerpo,

        })
        self.context = context

    def get_detalle_cabecera(self, form_cb):
        result = form_cb["list_result"]
        #_logger.error("MI VALOR 0: %r", self.get_name())
        return result
    def get_detalle_cuerpo(self, form_cp):
        result = form_cp["list_result1"]
        #_logger.error("MI VALOR 1: %r", name_text)
        return result

report_sxw.report_sxw('report.sunat_detraccion', 'sunat.adquiriente.proveedor.wizard', 'addons/sunat_detracciones/report/detraccion_txt.rml', parser=sunat_detraccion_adquiriente_txt, header=False)

