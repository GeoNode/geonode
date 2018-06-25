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

import os
import re
import fnmatch
import logging

from django.conf import settings
from django.template import loader
from django.contrib.staticfiles import finders


try:
    from importlib import import_module
except ImportError:
    from django.utils.importlib import import_module


try:
    from django.utils.six import string_types
except ImportError:
    string_types = (basestring,)
try:
    from django.template import Engine
except ImportError:
    class Engine(object):
        @staticmethod
        def get_default():
            return None

logger = logging.getLogger(__name__)

DEFAULT_BASE_TEMPLATE = "base.html"
DEFAULT_GEONODE_BASE_TEMPLATE = "geonode_base.html"


def get_template_loaders():
    try:
        return settings.TEMPLATE_LOADERS
    except BaseException:
        try:
            return settings.TEMPLATES[0]["OPTIONS"]["loaders"]
        except BaseException:
            try:
                from django.template.loader import get_template
                return [get_template(DEFAULT_BASE_TEMPLATE).origin.loader,
                        get_template(DEFAULT_GEONODE_BASE_TEMPLATE).origin.loader, ]
            except BaseException:
                return None


def find_all_templates(pattern='*.html'):
    """
    Finds all Django templates matching given glob in all TEMPLATE_LOADERS
    :param str pattern: `glob <http://docs.python.org/2/library/glob.html>`_
                        to match
    .. important:: At the moment egg loader is not supported.
    """
    templates = []
    template_loaders = flatten_template_loaders(get_template_loaders())
    if template_loaders:
        for loader_name in template_loaders:
            module, klass = loader_name.rsplit('.', 1)
            if loader_name in (
                'django.template.loaders.app_directories.Loader',
                'django.template.loaders.filesystem.Loader',
            ):
                loader_class = getattr(import_module(module), klass)
                try:
                    loader = loader_class(Engine.get_default())
                except BaseException:
                    loader = loader_class()
                for dir in loader.get_template_sources(''):
                    dir = "%s" % dir
                    for root, dirnames, filenames in os.walk(dir):
                        for basename in filenames:
                            filename = os.path.join(root, basename)
                            rel_filename = filename[len(dir) + 1:]
                            if fnmatch.fnmatch(filename, pattern) or \
                               fnmatch.fnmatch(basename, pattern) or \
                               fnmatch.fnmatch(rel_filename, pattern):
                                templates.append(filename)
            else:
                logger.debug('{0!s} is not supported'.format(loader_name))
    else:
        try:
            from django.template.loader import engines
            for engine in engines.all():
                for dir in engine.dirs:
                    for root, dirnames, filenames in os.walk(dir):
                        for basename in filenames:
                            filename = os.path.join(root, basename)
                            rel_filename = filename[len(dir) + 1:]
                            if fnmatch.fnmatch(filename, pattern) or \
                               fnmatch.fnmatch(basename, pattern) or \
                               fnmatch.fnmatch(rel_filename, pattern):
                                templates.append(filename)
        except BaseException:
            pass
    return sorted(set(templates))


def flatten_template_loaders(templates):
    """
    Given a collection of template loaders, unwrap them into one flat iterable.
    :param templates: template loaders to unwrap
    :return: template loaders as an iterable of strings.
    :rtype: generator expression
    """
    if templates:
        for template_loader in templates:
            if not isinstance(template_loader, string_types):
                import collections
                if isinstance(template_loader, collections.Iterable):
                    for subloader in flatten_template_loaders(template_loader):
                        yield subloader
                else:
                    yield "%s.%s" % (template_loader.__class__.__module__, template_loader.__class__.__name__)
            else:
                yield template_loader


theme_css_template = '@import "./{}.css";\n'
theme_css_template_regexp = '@import "\.\/{}\.css";\\n'

theme_html_template = '{{% extends "{}.html" %}}\n'
theme_html_template_regexp = '{{% extends "{}\.html" %}}\\n'


def activate_theme(theme):
    value = None
    geonode_base_css = finders.find('geonode/css/base.css')
    geonode_base_html = find_all_templates(pattern="geonode_base.html")

    if not theme.is_enabled and geonode_base_css and os.path.isfile(geonode_base_css):
        """
            Enable customized CSS;
             - look for GeoNode base.css file
             - render CSS from custom_theme_css.txt
               e.g.: theme-id-1-2018-04-06-082716806892.css
             - inject at the beginning of base.css the CSS import line
               e.g.: @import "./theme-id-1-2018-04-06-082716806892.css";
        """
        theme_css = os.path.join(os.path.dirname(geonode_base_css), "%s.css" % theme.theme_uuid)
        t = loader.get_template('admin/themes/custom_theme_css.txt')
        theme_css_content = t.render({'theme': theme})
        with open(theme_css, 'w') as f:
            f.write((u'%s' % theme_css_content).encode('utf-8').strip())
            f.close()
        if theme_css and os.path.isfile(theme_css):
            with open(geonode_base_css, 'r+') as base_css:
                value = base_css.read()
                theme_regexp = re.compile(theme_css_template_regexp.format(theme.theme_uuid))
                if theme_regexp.search(value):
                    value = theme_regexp.sub('', value)
                base_css.seek(0, 0)
                base_css.write(theme_css_template.format(theme.theme_uuid) + value)
                base_css.close()

    if not theme.is_enabled and geonode_base_html and os.path.isfile(geonode_base_html[0]):
        """
            Enable customized HTML;
             - look for GeoNode geonode_base.html file
             - render CSS from custom_theme_html.txt
               e.g.: theme-id-1-2018-04-06-082716806892.html
             - inject at the beginning of geonode_base.html the "extends" line
               e.g.: {% extends "theme/theme-id-1-2018-04-06-082716806892.html" %}
        """
        theme_html = os.path.join(os.path.dirname(geonode_base_html[0]), "%s.html" % theme.theme_uuid)
        t = loader.get_template('admin/themes/custom_theme_html.txt')

        custom_theme_base_header_template = find_all_templates(pattern="custom_theme_base_header.txt")
        hero_header_template = find_all_templates(pattern="custom_theme_hero_header.txt")
        hero_footer_template = find_all_templates(pattern="custom_theme_hero_footer.txt")
        bigsearch_header_template = find_all_templates(pattern="custom_theme_bigsearch_header.txt")
        bigsearch_footer_template = find_all_templates(pattern="custom_theme_bigsearch_footer.txt")
        partners_header_template = find_all_templates(pattern="custom_theme_partners_header.txt")
        partners_footer_template = find_all_templates(pattern="custom_theme_partners_footer.txt")
        contactus_header_template = find_all_templates(pattern="custom_theme_contactus_header.txt")
        contactus_footer_template = find_all_templates(pattern="custom_theme_contactus_footer.txt")
        footer_header_template = find_all_templates(pattern="custom_theme_footer_header.txt")
        footer_footer_template = find_all_templates(pattern="custom_theme_footer_footer.txt")

        def _read_template(template_file):
            if template_file and os.path.isfile(template_file[0]):
                with open(template_file[0], 'r') as f:
                    template_content = f.read()
                    f.close()
                    return template_content
            else:
                return ''

        custom_theme_base_header = _read_template(custom_theme_base_header_template)
        hero_header = _read_template(hero_header_template)
        hero_footer = _read_template(hero_footer_template)
        bigsearch_header = _read_template(bigsearch_header_template)
        bigsearch_footer = _read_template(bigsearch_footer_template)
        partners_header = _read_template(partners_header_template)
        partners_footer = _read_template(partners_footer_template)
        contactus_header = _read_template(contactus_header_template)
        contactus_footer = _read_template(contactus_footer_template)
        footer_header = _read_template(footer_header_template)
        footer_footer = _read_template(footer_footer_template)

        theme_html_content = t.render(
            {
                'theme': theme,
                'custom_base_header': custom_theme_base_header,
                'hero_header': hero_header,
                'hero_footer': hero_footer,
                'bigsearch_header': bigsearch_header,
                'bigsearch_footer': bigsearch_footer,
                'partners_header': partners_header,
                'partners_footer': partners_footer,
                'contactus_header': contactus_header,
                'contactus_footer': contactus_footer,
                'footer_header': footer_header,
                'footer_footer': footer_footer
            })
        with open(theme_html, 'w') as f:
            f.write((u'%s' % theme_html_content).encode('utf-8').strip())
            f.close()
        if theme_html and os.path.isfile(theme_html):
            with open(geonode_base_html[0], 'r+') as base_html:
                value = base_html.read()
                value = '{% comment %}' + value + '{% endcomment %}'
                theme_regexp = re.compile(theme_html_template_regexp.format(theme.theme_uuid))
                if theme_regexp.search(value):
                    value = theme_regexp.sub('', value)
                base_html.seek(0, 0)
                base_html.write(theme_html_template.format(theme.theme_uuid) + value)
                base_html.close()

    theme.is_enabled = True

    return value


def deactivate_theme(theme):
    value = None
    geonode_base_css = finders.find('geonode/css/base.css')
    geonode_base_html = find_all_templates(pattern="geonode_base.html")

    if theme.is_enabled and geonode_base_css and os.path.isfile(geonode_base_css):
        theme_css = os.path.join(os.path.dirname(geonode_base_css), "%s.css" % theme.theme_uuid)
        if theme_css and os.path.isfile(theme_css):
            """
                - Remove the customized CSS file
                - Restore "base.css" to its original state
            """
            os.remove(theme_css)
            with open(geonode_base_css, 'r+') as base_css:
                value = base_css.read()
                theme_regexp = re.compile(theme_css_template_regexp.format(theme.theme_uuid))
                if theme_regexp.search(value):
                    value = theme_regexp.sub('', value)
                base_css.seek(0, 0)
                base_css.write((u'%s' % value).encode('utf-8').strip())
                # base_css.truncate()
                base_css.close()

    if theme.is_enabled and geonode_base_html and os.path.isfile(geonode_base_html[0]):
        theme_html = os.path.join(os.path.dirname(geonode_base_html[0]), "%s.html" % theme.theme_uuid)
        if theme_html and os.path.isfile(theme_html):
            """
                - Remove the customized template file
                - Restore "geonode_base.html" to its original state
            """
            os.remove(theme_html)
            with open(geonode_base_html[0], 'r+') as base_html:
                value = base_html.read()
                value = re.sub(r'^.*{% comment %}(.*){% endcomment %}$',
                               r'\1',
                               value,
                               flags=re.DOTALL)
                base_html.seek(0, 0)
                base_html.write((u'%s' % value).encode('utf-8').strip())
                base_html.truncate()
                base_html.close()

    theme.is_enabled = False

    return value
