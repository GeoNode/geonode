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


# For client single page links
@register.simple_tag
def dataset_list_url():
    return hookset.dataset_list_url()


@register.simple_tag
def dataset_upload_url():
    return hookset.dataset_upload_url()


@register.simple_tag
def dataset_detail_url(layer):
    return hookset.dataset_detail_url(layer)


@register.simple_tag
def map_list_url():
    return hookset.map_list_url()


@register.simple_tag
def map_detail_url(map):
    return hookset.map_detail_url(map)


@register.simple_tag
def document_list_url():
    return hookset.document_list_url()


@register.simple_tag
def document_detail_url(document):
    return hookset.document_detail_url(document)


@register.simple_tag
def geoapp_list_url():
    return hookset.geoapp_list_url()


@register.simple_tag
def geoapp_detail_url(geoapp):
    return hookset.geoapp_detail_url(geoapp)


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
        if self.tag_name == "get_dataset_list":
            t = context.template.engine.get_template(hookset.dataset_list_template(context=context))
        elif self.tag_name == "get_dataset_detail":
            t = context.template.engine.get_template("geonode-mapstore-client/legacy/dataset_detail.html")
        elif self.tag_name == "get_dataset_new":
            t = context.template.engine.get_template(hookset.dataset_new_template(context=context))
        elif self.tag_name == "get_dataset_view":
            t = context.template.engine.get_template(hookset.dataset_view_template(context=context))
        elif self.tag_name == "get_dataset_edit":
            t = context.template.engine.get_template(hookset.dataset_edit_template(context=context))
        elif self.tag_name == "get_dataset_update":
            t = context.template.engine.get_template(hookset.dataset_update_template(context=context))
        elif self.tag_name == "get_dataset_embed":
            t = context.template.engine.get_template(hookset.dataset_embed_template(context=context))
        elif self.tag_name == "get_dataset_download":
            t = context.template.engine.get_template(hookset.dataset_download_template(context=context))
        elif self.tag_name == "get_dataset_style_edit":
            t = context.template.engine.get_template(hookset.dataset_style_edit_template(context=context))

        # MAPS
        if self.tag_name == "get_map_list":
            t = context.template.engine.get_template(hookset.map_list_template(context=context))
        elif self.tag_name == "get_map_detail":
            t = context.template.engine.get_template(hookset.map_detail_template(context=context))
        elif self.tag_name == "get_map_new":
            t = context.template.engine.get_template(hookset.map_new_template(context=context))
        elif self.tag_name == "get_map_view":
            t = context.template.engine.get_template(hookset.map_view_template(context=context))
        elif self.tag_name == "get_map_edit":
            t = context.template.engine.get_template(hookset.map_edit_template(context=context))
        elif self.tag_name == "get_map_update":
            t = context.template.engine.get_template(hookset.map_update_template(context=context))
        elif self.tag_name == "get_map_embed":
            t = context.template.engine.get_template("geonode-mapstore-client/map_embed.html")
        elif self.tag_name == "get_map_download":
            t = context.template.engine.get_template(hookset.map_download_template(context=context))

        # GEONODE_APPS
        if self.tag_name == "get_geoapp_list":
            t = context.template.engine.get_template(hookset.geoapp_list_template(context=context))
        elif self.tag_name == "get_geoapp_detail":
            t = context.template.engine.get_template(hookset.geoapp_detail_template(context=context))
        elif self.tag_name == "get_geoapp_new":
            t = context.template.engine.get_template(hookset.geoapp_new_template(context=context))
        elif self.tag_name == "get_geoapp_view":
            t = context.template.engine.get_template(hookset.geoapp_view_template(context=context))
        elif self.tag_name == "get_geoapp_edit":
            t = context.template.engine.get_template(hookset.geoapp_edit_template(context=context))
        elif self.tag_name == "get_geoapp_update":
            t = context.template.engine.get_template(hookset.geoapp_update_template(context=context))
        elif self.tag_name == "get_geoapp_embed":
            t = context.template.engine.get_template(hookset.geoapp_embed_template(context=context))
        elif self.tag_name == "get_geoapp_download":
            t = context.template.engine.get_template(hookset.geoapp_download_template(context=context))

        # 3DTILES

        if self.tag_name == "get_resourcebase_embed":
            t = context.template.engine.get_template(hookset.resourcebase_embed_template(context=context))

        if t:
            return t.render(context)
        else:
            return ""


def do_get_client_library_template(parser, token):
    tag_name, args, kwargs = parse_tag(token, parser)
    return GeoNodeClientLibraryTag(tag_name, args, kwargs)


register.tag("get_dataset_list", do_get_client_library_template)
register.tag("get_dataset_detail", do_get_client_library_template)
register.tag("get_dataset_new", do_get_client_library_template)
register.tag("get_dataset_view", do_get_client_library_template)
register.tag("get_dataset_edit", do_get_client_library_template)
register.tag("get_dataset_update", do_get_client_library_template)
register.tag("get_dataset_embed", do_get_client_library_template)
register.tag("get_dataset_download", do_get_client_library_template)
register.tag("get_dataset_style_edit", do_get_client_library_template)

register.tag("get_map_list", do_get_client_library_template)
register.tag("get_map_detail", do_get_client_library_template)
register.tag("get_map_new", do_get_client_library_template)
register.tag("get_map_view", do_get_client_library_template)
register.tag("get_map_edit", do_get_client_library_template)
register.tag("get_map_update", do_get_client_library_template)
register.tag("get_map_embed", do_get_client_library_template)
register.tag("get_map_download", do_get_client_library_template)

register.tag("get_geoapp_list", do_get_client_library_template)
register.tag("get_geoapp_detail", do_get_client_library_template)
register.tag("get_geoapp_new", do_get_client_library_template)
register.tag("get_geoapp_view", do_get_client_library_template)
register.tag("get_geoapp_edit", do_get_client_library_template)
register.tag("get_geoapp_update", do_get_client_library_template)
register.tag("get_geoapp_embed", do_get_client_library_template)
register.tag("get_geoapp_download", do_get_client_library_template)

register.tag("get_resourcebase_embed", do_get_client_library_template)
