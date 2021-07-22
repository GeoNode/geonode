#########################################################################
#
# Copyright (C) 2016 OSGeo
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

import re
import datetime
import json
from django.utils import timezone


class DefaultMangler(json.JSONDecoder):

    def __init__(self, *args, **kwargs):

        self.basepk = kwargs.get('basepk', -1)
        self.owner = kwargs.get('owner', 'admin')
        self.datastore = kwargs.get('datastore', '')
        self.siteurl = kwargs.get('siteurl', '')

        super().__init__(*args)

    def default(self, obj):
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

    def decode(self, json_string):
        """
        json_string is basicly string that you give to json.loads method
        """
        default_obj = super().decode(json_string)

        # manipulate your object any way you want
        # ....

        return default_obj


class ResourceBaseMangler(DefaultMangler):

    def default(self, obj):
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

    def decode(self, json_string):
        """
        json_string is basicly string that you give to json.loads method
        """
        default_obj = super().decode(json_string)

        # manipulate your object any way you want
        # ....
        upload_sessions = []
        for obj in default_obj:
            obj['pk'] = obj['pk'] + self.basepk

            obj['fields']['featured'] = False
            obj['fields']['rating'] = 0
            obj['fields']['popular_count'] = 0
            obj['fields']['share_count'] = 0
            obj['fields']['is_published'] = True
            obj['fields']['thumbnail_url'] = ''

            if 'distribution_url' in obj['fields']:
                if not obj['fields']['distribution_url'] is None and 'layers' in obj['fields']['distribution_url']:

                    obj['fields']['polymorphic_ctype'] = ["layers", "layer"]

                    try:
                        p = '(?P<protocol>http.*://)?(?P<host>[^:/ ]+).?(?P<port>[0-9]*)(?P<details_url>.*)'
                        m = re.search(p, obj['fields']['distribution_url'])
                        if 'http' in m.group('protocol'):
                            obj['fields']['detail_url'] = self.siteurl + m.group('details_url')
                        else:
                            obj['fields']['detail_url'] = self.siteurl + obj['fields']['distribution_url']
                    except Exception:
                        obj['fields']['detail_url'] = obj['fields']['distribution_url']

                else:
                    obj['fields']['polymorphic_ctype'] = ["maps", "map"]

            try:
                obj['fields'].pop("distribution_description", None)
            except Exception:
                pass

            try:
                obj['fields'].pop("distribution_url", None)
            except Exception:
                pass

            try:
                obj['fields'].pop("thumbnail", None)
            except Exception:
                pass

            upload_sessions.append(self.add_upload_session(obj['pk'], obj['fields']['owner']))

        default_obj.extend(upload_sessions)

        return default_obj

    def add_upload_session(self, pk, owner):
        obj = dict()

        obj['pk'] = pk
        obj['model'] = 'datasets.uploadsession'

        obj['fields'] = dict()
        obj['fields']['user'] = owner
        obj['fields']['traceback'] = None
        obj['fields']['context'] = None
        obj['fields']['error'] = None
        obj['fields']['processed'] = True
        obj['fields']['date'] = datetime.datetime.now(timezone.get_current_timezone()).strftime("%Y-%m-%dT%H:%M:%S")

        return obj


class LayerMangler(DefaultMangler):

    def default(self, obj):
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

    def decode(self, json_string):
        """
        json_string is basicly string that you give to json.loads method
        """
        default_obj = super().decode(json_string)

        # manipulate your object any way you want
        # ....
        for obj in default_obj:
            obj['pk'] = obj['pk'] + self.basepk

            # Retrieve the ResourceBase associated to this Dataset
            from geonode.base.models import ResourceBase

            resource = ResourceBase.objects.get(pk=obj['pk'])

            obj['fields']['upload_session'] = obj['pk']
            obj['fields']['service'] = None
            obj['fields']['charset'] = "UTF-8"
            obj['fields']['title_en'] = resource.title
            obj['fields']['data_quality_statement_en'] = ""
            obj['fields']['regions'] = []
            obj['fields']['supplemental_information_en'] = "No information provided"
            obj['fields']['abstract_en'] = "No abstract provided"
            obj['fields']['purpose_en'] = ""
            obj['fields']['constraints_other_en'] = ""
            obj['fields']['default_style'] = None

            if self.datastore:
                obj['fields']['store'] = self.datastore
            else:
                obj['fields']['store'] = obj['fields']['name']

            try:
                obj['fields'].pop("popular_count", None)
            except Exception:
                pass

            try:
                obj['fields'].pop("share_count", None)
            except Exception:
                pass

            try:
                obj['fields'].pop("title", None)
            except Exception:
                pass

        return default_obj


class LayerAttributesMangler(DefaultMangler):

    def default(self, obj):
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

    def decode(self, json_string):
        """
        json_string is basicly string that you give to json.loads method
        """
        default_obj = super().decode(json_string)

        # manipulate your object any way you want
        # ....
        for obj in default_obj:
            obj['pk'] = obj['pk'] + self.basepk

            obj['fields']['layer'] = obj['fields']['layer'] + self.basepk

        return default_obj


class MapMangler(DefaultMangler):

    def default(self, obj):
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

    def decode(self, json_string):
        """
        json_string is basicly string that you give to json.loads method
        """
        default_obj = super().decode(json_string)

        # manipulate your object any way you want
        # ....
        for obj in default_obj:
            obj['pk'] = obj['pk'] + self.basepk

            # Retrieve the ResourceBase associated to this Dataset
            from geonode.base.models import ResourceBase

            resource = ResourceBase.objects.get(pk=obj['pk'])

            obj['fields']['urlsuffix'] = ""
            obj['fields']['title_en'] = resource.title
            obj['fields']['featuredurl'] = ""
            obj['fields']['data_quality_statement_en'] = None
            obj['fields']['supplemental_information_en'] = "No information provided"
            obj['fields']['abstract_en'] = ""
            obj['fields']['purpose_en'] = None
            obj['fields']['constraints_other_en'] = None

            try:
                obj['fields'].pop("popular_count", None)
            except Exception:
                pass

            try:
                obj['fields'].pop("share_count", None)
            except Exception:
                pass

            try:
                obj['fields'].pop("title", None)
            except Exception:
                pass

        return default_obj


class MapLayersMangler(DefaultMangler):

    def default(self, obj):
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

    def decode(self, json_string):
        """
        json_string is basicly string that you give to json.loads method
        """
        default_obj = super().decode(json_string)

        # manipulate your object any way you want
        # ....
        for obj in default_obj:
            obj['pk'] = obj['pk'] + self.basepk

            obj['fields']['map'] = obj['fields']['map'] + self.basepk

        return default_obj
