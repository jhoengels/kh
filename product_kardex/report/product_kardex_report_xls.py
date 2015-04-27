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


import xlwt
import time
from datetime import datetime
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls

from openerp.addons.report_xls.utils import rowcol_to_cell, _render

from openerp.tools.translate import translate, _
import logging
_logger = logging.getLogger(__name__)

_ir_translation_name = 'product.kardex.xls' # To DO : create translation table

class product_kardex_print_xls(report_sxw.rml_parse):
           
    def __init__(self, cr, uid, name, context):
        if context is None:
            context = {}
        super(product_kardex_print_xls, self).__init__(cr, uid, name, context=context)
        self.context = context
        self.localcontext.update({
            '_': self._,
        })

    def _(self, src):
        lang = self.context.get('lang', 'en_US')
        return translate(
            self.cr, _ir_translation_name, 'report', lang, src) or src


class product_kardex_xls(report_xls):
    def __init__(self, name, table, rml=False, parser=False, header=True, store=False):
        super(product_kardex_xls, self).__init__(name, table, rml, parser, header, store)
        # Cell Styles
        _xs = self.xls_styles
        

    def generate_xls_report(self, _p, _xs, form, objects, wb):
        ws = wb.add_sheet('Kardex movimiento',cell_overwrite_ok=True)
        #ws.write(1,3,'TOTALES')
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0

        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']
        
        # Title
        cell_style = xlwt.easyxf(_xs['xls_title'])
        report_name =  'KARDEX DE MOVIMIENTO DE PRODUCTO POR ALMACEN'
        c_specs = [('report_name', 1, 0, 'text', report_name),]       
        row_data = self.xls_row_template(c_specs, ['report_name'])
        row_pos = self.xls_write_row(ws, row_pos, row_data, row_style=cell_style)
        

product_kardex_xls('report.kardex.product.xls', 'stock.move', parser=product_kardex_print_xls)
