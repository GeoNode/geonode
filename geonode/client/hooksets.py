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


class BaseHookSet:
    # Layers
    def dataset_list_template(self, context=None):
        return NotImplemented

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
        return NotImplemented

    def dataset_upload_url(self):
        return NotImplemented

    def dataset_detail_url(self, layer):
        return NotImplemented

    # Maps
    def map_list_template(self, context=None):
        return NotImplemented

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
        return NotImplemented

    def map_detail_url(self, map):
        return NotImplemented

    # GeoApps
    def geoapp_list_template(self, context=None):
        return NotImplemented

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
        return NotImplemented

    def geoapp_detail_url(self, geoapp):
        return NotImplemented

    def resourcebase_embed_template(self, context=None):
        return None

    # Documents
    def document_list_url(self):
        return NotImplemented

    def document_detail_url(self, document):
        return NotImplemented

    # Map Persisting
    def viewer_json(self, conf, context=None):
        if isinstance(conf, str):
            conf = json.loads(conf)
        return conf

    def update_from_viewer(self, conf, context=None):
        return NotImplemented

    def metadata_update_redirect(self, url, request=None):
        if "metadata_uri" in url:
            return url.replace("/metadata_uri", "")
        return url.replace("/metadata", "")

    def get_absolute_url(self, context=None):
        return None
