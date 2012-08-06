# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django import template

register = template.Library()

class HasObjPermNode(template.Node):
    def __init__(self, user, obj, perm, varname):
        self.user = template.Variable(user)
        self.obj = template.Variable(obj)
        self.perm = perm
        self.varname = varname

    def render(self, context):
        user = self.user.resolve(context)
        obj = self.obj.resolve(context)
        context[self.varname] = user.has_perm(self.perm, obj=obj)
        return ''

def _check_quoted(string):
    return string[0] == '"' and string[-1] == '"'

@register.tag('has_obj_perm')
def do_has_obj_perm(parser, token):
    """
    {% has_obj_perm user obj "app.view_thing" as can_view_thing %}
    """
    args = token.split_contents()[1:]
    return HasObjPermNode(args[0], args[1], args[2][1:-1], args[4])
