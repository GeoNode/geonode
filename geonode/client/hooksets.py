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
import json

from django.conf import settings
from django.urls.base import reverse


class BaseHookSet:

    # Layers
    def dataset_list_template(self, context=None):
        return 'datasets/dataset_list_default.html'

    def dataset_detail_template(self, context=None):
        return NotImplemented

    def dataset_new_template(self, context=None):
        return NotImplemented

    def dataset_view_template(self, context=None):
        return NotImplemented

    def dataset_edit_template(self, context=None):
        return NotImplemented

    def dataset_update_template(self, context=None):
        return NotImplemented

    def dataset_embed_template(self, context=None):
        return NotImplemented

    def dataset_download_template(self, context=None):
        return NotImplemented

    def dataset_style_edit_template(self, context=None):
        return NotImplemented

    def dataset_list_url(self):
        return self.add_limit_settings(reverse('dataset_browse'))

    def dataset_detail_url(self, layer):
        return reverse('dataset_detail', args=(layer.alternate,))

    # Maps
    def map_list_template(self, context=None):
        return 'maps/map_list_default.html'

    def map_detail_template(self, context=None):
        return NotImplemented

    def map_new_template(self, context=None):
        return NotImplemented

    def map_view_template(self, context=None):
        return NotImplemented

    def map_edit_template(self, context=None):
        return NotImplemented

    def map_update_template(self, context=None):
        return NotImplemented

    def map_embed_template(self, context=None):
        return NotImplemented

    def map_download_template(self, context=None):
        return NotImplemented

    def map_list_url(self):
        return self.add_limit_settings(reverse('maps_browse'))

    def map_detail_url(self, map):
        return reverse('map_detail', args=(map.id,))

    # GeoApps
    def geoapp_list_template(self, context=None):
        return 'apps/app_list_default.html'

    def geoapp_detail_template(self, context=None):
        return NotImplemented

    def geoapp_new_template(self, context=None):
        return NotImplemented

    def geoapp_view_template(self, context=None):
        return NotImplemented

    def geoapp_edit_template(self, context=None):
        return NotImplemented

    def geoapp_update_template(self, context=None):
        return NotImplemented

    def geoapp_embed_template(self, context=None):
        return NotImplemented

    def geoapp_download_template(self, context=None):
        return NotImplemented

    def geoapp_list_url(self):
        return self.add_limit_settings(reverse('apps_browse'))

    def geoapp_detail_url(self, geoapp):
        return reverse('geoapp_detail', args=(geoapp.id,))

    # Documents
    def document_list_url(self):
        return self.add_limit_settings(reverse('document_browse'))

    def document_detail_url(self, document):
        return reverse('document_detail', args=(document.id,))

    # Map Persisting
    def viewer_json(self, conf, context=None):
        if isinstance(conf, str):
            conf = json.loads(conf)
        return conf

    def update_from_viewer(self, conf, context=None):
        conf = self.viewer_json(conf, context=context)
        context['config'] = conf
        return 'maps/map_edit.html'

    def add_limit_settings(self, url):
        CLIENT_RESULTS_LIMIT = settings.CLIENT_RESULTS_LIMIT
        return f"{url}?limit={CLIENT_RESULTS_LIMIT}"

    def metadata_update_redirect(self, url):
        if "metadata_uri" in url:
            return url.replace('/metadata_uri', '')
        return url.replace('/metadata', '')
