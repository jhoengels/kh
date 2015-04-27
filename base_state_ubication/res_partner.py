# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
# Copyright (c) 2012 Cubic ERP - Teradata SAC. (http://cubicerp.com).
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import fields, osv


class res_partner(osv.osv):
    
    _name = 'res.partner'
    _inherit = 'res.partner'
    _columns = {
        'state_id': fields.many2one("res.country.state", 'Ubication', domain="[('country_id','=',country_id),('type','=','normal')]"),
        }

    def _display_address(self, cr, uid, address, without_company=False, context=None):

        '''
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.

        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        '''

        # get the information that will be injected into the display format
        # get the address format
        #address_format = address.country_id and address.country_id.address_format or \
        #      "%(street)s\n%(street2)s\n%(state_code)s %(state_complete_name)s\n%(country_name)s"

        address_format = address.country_id and address.country_id.address_format or \
              "%(street)s\n %(state_complete_name)s\n%(country_name)s"

        args = {
            'state_code': address.state_id and address.state_id.code or '',
            'state_name': address.state_id and address.state_id.name or '',
            'state_complete_name': address.state_id and address.state_id.complete_name or '',
            'country_code': address.country_id and address.country_id.code or '',
            'country_name': address.country_id and address.country_id.name or '',
            'company_name': address.parent_id and address.parent_id.name or '',
        }
        for field in self._address_fields(cr, uid, context=context):
            args[field] = getattr(address, field) or ''
        if without_company:
            args['company_name'] = ''
        elif address.parent_id:
            address_format = '%(company_name)s\n' + address_format
        return address_format % args

res_partner()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: