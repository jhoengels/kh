# -*- coding: utf-8 -*-
###############################################################################~!!~~!!!
#
# Copyright (c) 2010-2012, OPENTIA Group (<http://opentia.com>)
# The word "OPENTIA" is an European Community Trademark property of the Opentia Group
#
# @author: Opentia "Happy Hacking" Team
# @e-mail: consultoria@opentia·es
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################~!!~~!!!
{
    'name' : '''Remove 'Force Availability' ''',
    'description' : '''
       · Removes the 'Force Availability' button from Picking form view
    ''',
    'version' : '0.1',
    'depends' : ["stock",],
    'category': 'Warehouse',
    'author' : 'OPENTIA',
    'url': 'http://www.opentia.com/',
    'website': 'http://www.opentia.com/',
    'data': [],
    'update_xml': ['stock_view.xml','security/security.xml',],
    'init_xml': [],
    'installable' : True,
    'active' : False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

