# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2018 OSGeo
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
from django.conf import settings
from django.template.base import FilterExpression, kwarg_re
from ..hooks import hookset

register = template.Library()


@register.simple_tag
def mapbox_access_token():
    return getattr(settings, "MAPBOX_ACCESS_TOKEN", None)


@register.simple_tag
def bing_api_key():
    return getattr(settings, "BING_API_KEY", None)


@register.simple_tag
def google_api_key():
    return getattr(settings, "GOOGLE_API_KEY", None)


def parse_tag(token, parser):
    """
    Generic template tag parser.

    Returns a three-tuple: (tag_name, args, kwargs)

    tag_name is a string, the name of the tag.

    args is a list of FilterExpressions, from all the arguments that didn't look like kwargs,
    in the order they occurred, including any that were mingled amongst kwargs.

    kwargs is a dictionary mapping kwarg names to FilterExpressions, for all the arguments that
    looked like kwargs, including any that were mingled amongst args.

    (At rendering time, a FilterExpression f can be evaluated by calling f.resolve(context).)
    """
    # Split the tag content into words, respecting quoted strings.
    bits = token.split_contents()

    # Pull out the tag name.
    tag_name = bits.pop(0)

    # Parse the rest of the args, and build FilterExpressions from them so that
    # we can evaluate them later.
    args = []
    kwargs = {}
    for bit in bits:
        # Is this a kwarg or an arg?
        match = kwarg_re.match(bit)
        kwarg_format = match and match.group(1)
        if kwarg_format:
            key, value = match.groups()
            kwargs[key] = FilterExpression(value, parser)
        else:
            args.append(FilterExpression(bit, parser))

    return (tag_name, args, kwargs)


class GeoNodeClientLibraryTag(template.Node):
    def __init__(self, tag_name, *args, **kwargs):
        self.tag_name = tag_name

    def render(self, context):
        t = None

        # LAYERS
        if self.tag_name == 'get_layer_list':
            t = context.template.engine.get_template(
                hookset.layer_list_template(
                    context=context))
        elif self.tag_name == 'get_layer_detail':
            t = context.template.engine.get_template(
                hookset.layer_detail_template(
                    context=context))
        elif self.tag_name == 'get_layer_new':
            t = context.template.engine.get_template(
                hookset.layer_new_template(
                    context=context))
        elif self.tag_name == 'get_layer_view':
            t = context.template.engine.get_template(
                hookset.layer_view_template(
                    context=context))
        elif self.tag_name == 'get_layer_edit':
            t = context.template.engine.get_template(
                hookset.layer_edit_template(
                    context=context))
        elif self.tag_name == 'get_layer_update':
            t = context.template.engine.get_template(
                hookset.layer_update_template(
                    context=context))
        elif self.tag_name == 'get_layer_embed':
            t = context.template.engine.get_template(
                hookset.layer_embed_template(
                    context=context))
        elif self.tag_name == 'get_layer_download':
            t = context.template.engine.get_template(
                hookset.layer_download_template(
                    context=context))
        elif self.tag_name == 'get_layer_style_edit':
            t = context.template.engine.get_template(
                hookset.layer_style_edit_template(
                    context=context))

        # MAPS
        if self.tag_name == 'get_map_list':
            t = context.template.engine.get_template(
                hookset.map_list_template(
                    context=context))
        elif self.tag_name == 'get_map_detail':
            t = context.template.engine.get_template(
                hookset.map_detail_template(
                    context=context))
        elif self.tag_name == 'get_map_new':
            t = context.template.engine.get_template(
                hookset.map_new_template(
                    context=context))
        elif self.tag_name == 'get_map_view':
            t = context.template.engine.get_template(
                hookset.map_view_template(
                    context=context))
        elif self.tag_name == 'get_map_edit':
            t = context.template.engine.get_template(
                hookset.map_edit_template(
                    context=context))
        elif self.tag_name == 'get_map_update':
            t = context.template.engine.get_template(
                hookset.map_update_template(
                    context=context))
        elif self.tag_name == 'get_map_embed':
            t = context.template.engine.get_template(
                hookset.map_embed_template(
                    context=context))
        elif self.tag_name == 'get_map_download':
            t = context.template.engine.get_template(
                hookset.map_download_template(
                    context=context))

        if t:
            return t.render(context)
        else:
            return ''


def do_get_client_library_template(parser, token):
    tag_name, args, kwargs = parse_tag(token, parser)
    return GeoNodeClientLibraryTag(tag_name, args, kwargs)


register.tag('get_layer_list', do_get_client_library_template)
register.tag('get_layer_detail', do_get_client_library_template)
register.tag('get_layer_new', do_get_client_library_template)
register.tag('get_layer_view', do_get_client_library_template)
register.tag('get_layer_edit', do_get_client_library_template)
register.tag('get_layer_update', do_get_client_library_template)
register.tag('get_layer_embed', do_get_client_library_template)
register.tag('get_layer_download', do_get_client_library_template)
register.tag('get_layer_style_edit', do_get_client_library_template)

register.tag('get_map_list', do_get_client_library_template)
register.tag('get_map_detail', do_get_client_library_template)
register.tag('get_map_new', do_get_client_library_template)
register.tag('get_map_view', do_get_client_library_template)
register.tag('get_map_edit', do_get_client_library_template)
register.tag('get_map_update', do_get_client_library_template)
register.tag('get_map_embed', do_get_client_library_template)
register.tag('get_map_download', do_get_client_library_template)
