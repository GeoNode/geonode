#########################################################################
#
# Copyright (C) 2021 OSGeo
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
import uuid
import logging
import datetime
import traceback

from urllib.parse import urlparse, urljoin

from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import FieldDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.contrib.gis.geos import (
    GEOSGeometry,
    MultiPolygon)

from geonode.utils import OGC_Servers_Handler

from ..base import enumerations
from ..base.models import (
    ExtraMetadata,
    Link,
    Region,
    License,
    ResourceBase,
    TopicCategory,
    ThesaurusKeyword,
    HierarchicalKeyword,
    SpatialRepresentationType)

from ..layers.models import Dataset
from ..documents.models import Document
from ..documents.enumerations import (
    DOCUMENT_TYPE_MAP,
    DOCUMENT_MIMETYPE_MAP)
from ..people.utils import get_valid_user
from ..layers.utils import resolve_regions
from ..layers.metadata import convert_keyword

logger = logging.getLogger(__name__)

ogc_settings = OGC_Servers_Handler(settings.OGC_SERVER)['default']


class KeywordHandler:
    '''
    Object needed to handle the keywords coming from the XML
    The expected input are:
     - instance (Dataset/Document/Map): instance of any object inherited from ResourceBase.
     - keywords (list(dict)): Is required to analyze the keywords to find if some thesaurus is available.
    '''

    def __init__(self, instance, keywords):
        self.instance = instance
        self.keywords = keywords

    def set_keywords(self):
        '''
        Method with the responsible to set the keywords (free and thesaurus) to the object.
        At return there is always a call to final_step to let it hookable.
        '''
        keywords, tkeyword = self.handle_metadata_keywords()
        self._set_free_keyword(keywords)
        self._set_tkeyword(tkeyword)
        return self.instance

    def handle_metadata_keywords(self):
        '''
        Method the extract the keyword from the dict.
        If the keyword are passed, try to extract them from the dict
        by splitting free-keyword from the thesaurus
        '''
        fkeyword = []
        tkeyword = []
        if len(self.keywords) > 0:
            for dkey in self.keywords:
                if isinstance(dkey, HierarchicalKeyword):
                    fkeyword += [dkey.name]
                    continue
                if isinstance(dkey, str):
                    fkeyword += [dkey]
                    continue
                if dkey['type'] == 'place':
                    continue
                thesaurus = dkey['thesaurus']
                if thesaurus['date'] or thesaurus['datetype'] or thesaurus['title']:
                    for k in dkey['keywords']:
                        tavailable = self.is_thesaurus_available(thesaurus, k)
                        if tavailable.exists():
                            tkeyword += [tavailable.first()]
                        else:
                            fkeyword += [k]
                else:
                    fkeyword += dkey['keywords']
            return fkeyword, tkeyword
        return self.keywords, []

    @staticmethod
    def is_thesaurus_available(thesaurus, keyword):
        is_available = ThesaurusKeyword.objects.filter(alt_label=keyword).filter(thesaurus__title=thesaurus['title'])
        return is_available

    def _set_free_keyword(self, keywords):
        if len(keywords) > 0:
            if self.instance.keywords.exists():
                self.instance.keywords.clear()
            self.instance.keywords.add(*keywords)
        return keywords

    def _set_tkeyword(self, tkeyword):
        if len(tkeyword) > 0:
            if self.instance.tkeywords.exists():
                self.instance.tkeywords.clear()
            self.instance.tkeywords.add(*tkeyword)
        return [t.alt_label for t in tkeyword]


def update_resource(instance: ResourceBase, xml_file: str = None, regions: list = [], keywords: list = [], vals: dict = {}, extra_metadata: list = []):

    if xml_file:
        instance.metadata_xml = open(xml_file).read()

    regions_resolved, regions_unresolved = resolve_regions(regions)
    _keywords = keywords.copy()
    _keywords.extend(convert_keyword(regions_unresolved))

    # Assign the regions (needs to be done after saving)
    regions_resolved = list(set(regions_resolved))
    if regions_resolved:
        if len(regions_resolved) > 0:
            if not instance.regions:
                instance.regions = regions_resolved
            else:
                instance.regions.clear()
                instance.regions.add(*regions_resolved)

    instance = KeywordHandler(instance, _keywords).set_keywords()

    # set model properties
    defaults = {}
    if vals:
        for key, value in vals.items():
            if key == 'spatial_representation_type':
                spatial_repr = SpatialRepresentationType.objects.filter(identifier=value)
                if value is not None and spatial_repr.exists():
                    value = SpatialRepresentationType(identifier=value)
                # if the SpatialRepresentationType is not available in the DB, we just set it as None
                elif value is not None and not spatial_repr.exists():
                    value = None
                defaults[key] = value
            elif key == 'topic_category':
                value, created = TopicCategory.objects.get_or_create(
                    identifier=value,
                    defaults={'description': '', 'gn_description': value})
                key = 'category'
                defaults[key] = value
            else:
                defaults[key] = value

    poc = defaults.pop('poc', None)
    metadata_author = defaults.pop('metadata_author', None)

    to_update = {}
    for _key in ('name', ):
        try:
            instance._meta.get_field(_key)
            if _key in defaults:
                to_update[_key] = defaults.pop(_key)
            else:
                to_update[_key] = getattr(instance, _key)
        except FieldDoesNotExist:
            if _key in defaults:
                defaults.pop(_key)

    # Save all the modified information in the instance without triggering signals.
    _default_values = {
        'date': timezone.now(),
        'title': getattr(instance, 'name', ''),
        'abstract': ''
    }
    for _key in _default_values.keys():
        if not defaults.get(_key, None):
            try:
                instance._meta.get_field(_key)
                defaults[_key] = getattr(instance, _key, None) or _default_values.get(_key)
            except FieldDoesNotExist:
                if _key in defaults:
                    defaults.pop(_key)

    if isinstance(instance, Dataset):
        for _key in ('workspace', 'store', 'subtype', 'alternate', 'typename'):
            if hasattr(instance, _key):
                if _key in defaults:
                    to_update[_key] = defaults.pop(_key)
                else:
                    to_update[_key] = getattr(instance, _key)
            elif _key in defaults:
                defaults.pop(_key)
    if isinstance(instance, Document):
        if 'links' in defaults:
            defaults.pop('links')
        for _key in ('subtype', 'doc_url', 'doc_file', 'extension'):
            if hasattr(instance, _key):
                if _key in defaults:
                    to_update[_key] = defaults.pop(_key)
                else:
                    to_update[_key] = getattr(instance, _key)
            elif _key in defaults:
                defaults.pop(_key)

    if hasattr(instance, 'charset') and 'charset' not in to_update:
        to_update['charset'] = defaults.pop('charset', instance.charset)
    if hasattr(instance, 'subtype') and 'subtype' not in to_update:
        to_update['subtype'] = defaults.pop('subtype', instance.subtype)
    if hasattr(instance, 'urlsuffix') and 'urlsuffix' not in to_update:
        to_update['urlsuffix'] = defaults.pop('urlsuffix', instance.urlsuffix)
    if hasattr(instance, 'ows_url') and 'ows_url' not in to_update:
        _default_ows_url = urljoin(ogc_settings.PUBLIC_LOCATION, 'ows')
        to_update['ows_url'] = defaults.pop('ows_url', getattr(instance, 'ows_url', None)) or _default_ows_url

    to_update.update(defaults)
    try:
        ResourceBase.objects.filter(id=instance.resourcebase_ptr.id).update(**defaults)
    except Exception as e:
        logger.error(f"{e} - {defaults}")
        raise
    try:
        instance.get_real_concrete_instance_class().objects.filter(id=instance.id).update(**to_update)
    except Exception as e:
        logger.error(f"{e} - {to_update}")
        raise

    # Check for "remote services" availability
    from ..services.models import Service
    from ..harvesting.models import HarvestableResource

    if HarvestableResource.objects.filter(geonode_resource__uuid=instance.uuid).exists():
        _h = HarvestableResource.objects.filter(geonode_resource__uuid=instance.uuid).get().harvester
        if Service.objects.filter(harvester=_h).exists():
            _s = Service.objects.filter(harvester=_h).get()
            _to_update = {
                "remote_typename": _s.name,
                # "ows_url": _s.service_url,
                "subtype": 'remote'
            }
            if hasattr(instance, 'remote_service'):
                _to_update["remote_service"] = _s
            instance.get_real_concrete_instance_class().objects.filter(id=instance.id).update(**_to_update)

    # Refresh from DB
    instance.refresh_from_db()
    if poc:
        instance.poc = poc
    if metadata_author:
        instance.metadata_author = metadata_author

    if extra_metadata:
        instance.metadata.all().delete()
        for _m in extra_metadata:
            new_m = ExtraMetadata.objects.create(
                resource=instance,
                metadata=_m
            )
            instance.metadata.add(new_m)

    return instance


def metadata_storers(instance, custom={}):
    from django.utils.module_loading import import_string
    available_storers = (
        settings.METADATA_STORERS
        if hasattr(settings, "METADATA_STORERS")
        else []
    )
    for storer_path in available_storers:
        storer = import_string(storer_path)
        storer(instance, custom)
    return instance


def get_alternate_name(instance):
    try:
        if isinstance(instance, Dataset):
            from ..services.enumerations import CASCADED
            from ..services.enumerations import INDEXED

            # these are only used if there is no user-configured value in the settings
            _DEFAULT_CASCADE_WORKSPACE = "cascaded-services"
            _DEFAULT_WORKSPACE = "geonode"

            if hasattr(instance, 'remote_service') and instance.remote_service is not None and instance.remote_service.method == INDEXED:
                result = instance.name
            elif hasattr(instance, 'remote_service') and instance.remote_service is not None and instance.remote_service.method == CASCADED:
                _ws = getattr(settings, "CASCADE_WORKSPACE", _DEFAULT_CASCADE_WORKSPACE)
                result = f"{_ws}:{instance.name}"
            else:
                if hasattr(instance, 'sourcetype') and instance.sourcetype != enumerations.SOURCE_TYPE_LOCAL:
                    _ws = instance.workspace
                else:
                    # we are not dealing with a service-related instance
                    _ws = instance.workspace or getattr(settings, "DEFAULT_WORKSPACE", _DEFAULT_WORKSPACE)
                result = f"{_ws}:{instance.name}" if _ws else f"{instance.name}"
            return result
    except Exception as e:
        logger.debug(e)
    return instance.alternate


def get_related_resources(document):
    if document.links:
        try:
            return [
                link.content_type.get_object_for_this_type(id=link.object_id)
                for link in document.links.all()
            ]
        except Exception:
            return []
    else:
        return []


def document_post_save(instance, *args, **kwargs):
    instance.csw_type = 'document'

    if instance.files:
        _, extension = os.path.splitext(os.path.basename(instance.files[0]))
        instance.extension = extension[1:]
        doc_type_map = DOCUMENT_TYPE_MAP
        doc_type_map.update(getattr(settings, 'DOCUMENT_TYPE_MAP', {}))
        if doc_type_map is None:
            subtype = 'other'
        else:
            subtype = doc_type_map.get(
                instance.extension.lower(), 'other')
        instance.subtype = subtype
    elif instance.doc_url:
        if '.' in urlparse(instance.doc_url).path:
            instance.extension = urlparse(instance.doc_url).path.rsplit('.')[-1]

    name = None
    ext = instance.extension
    mime_type_map = DOCUMENT_MIMETYPE_MAP
    mime_type_map.update(getattr(settings, 'DOCUMENT_MIMETYPE_MAP', {}))
    mime = mime_type_map.get(ext, 'text/plain')
    url = None

    if instance.id and instance.files:
        name = "Hosted Document"
        site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
        url = f"{site_url}{reverse('document_download', args=(instance.id,))}"
    elif instance.doc_url:
        name = "External Document"
        url = instance.doc_url

    Document.objects.filter(id=instance.id).update(
        extension=instance.extension,
        subtype=instance.subtype,
        doc_url=instance.doc_url,
        csw_type=instance.csw_type)

    if name and url and ext:
        Link.objects.get_or_create(
            resource=instance.resourcebase_ptr,
            url=url,
            defaults=dict(
                extension=ext,
                name=name,
                mime=mime,
                url=url,
                link_type='data',))

    resources = get_related_resources(instance)

    # if there are (new) linked resources update the bbox computed by their bboxes
    if resources:
        bbox = MultiPolygon([r.bbox_polygon for r in resources])
        instance.set_bbox_polygon(bbox.extent, instance.srid)
    elif not instance.bbox_polygon:
        instance.set_bbox_polygon((-180, -90, 180, 90), 'EPSG:4326')


def dataset_post_save(instance, *args, **kwargs):
    base_file, info = instance.get_base_file()

    if info:
        instance.info = info

    from ..layers.models import vec_exts, cov_exts
    if base_file is not None:
        extension = f'.{base_file.name}'
        if extension in vec_exts:
            instance.subtype = 'vector'
        elif extension in cov_exts:
            instance.subtype = 'raster'

    Dataset.objects.filter(id=instance.id).update(subtype=instance.subtype)


def metadata_post_save(instance, *args, **kwargs):
    logger.debug("handling UUID In pre_save_dataset")
    defaults = {}
    if isinstance(instance, Dataset) and hasattr(settings, 'LAYER_UUID_HANDLER') and settings.LAYER_UUID_HANDLER != '':
        logger.debug("using custom uuid handler In pre_save_dataset")
        from ..layers.utils import get_uuid_handler
        _uuid = get_uuid_handler()(instance).create_uuid()
        if _uuid != instance.uuid:
            instance.uuid = _uuid
            Dataset.objects.filter(id=instance.id).update(uuid=_uuid)

    # Set a default user for accountstream to work correctly.
    if instance.owner is None:
        instance.owner = get_valid_user()

    if not instance.uuid:
        instance.uuid = str(uuid.uuid4())

    # set default License if no specified
    if instance.license is None:
        license = License.objects.filter(name="Not Specified")
        if license and len(license) > 0:
            instance.license = license[0]

    instance.thumbnail_url = instance.get_real_instance().get_thumbnail_url()
    instance.csw_insert_date = datetime.datetime.now(timezone.get_current_timezone())
    instance.set_missing_info()

    defaults = dict(
        uuid=instance.uuid,
        owner=instance.owner,
        license=instance.license,
        alternate=instance.alternate,
        thumbnail_url=instance.thumbnail_url,
        csw_insert_date=instance.csw_insert_date
    )

    # Fixup bbox
    if instance.bbox_polygon is None:
        instance.set_bbox_polygon((-180, -90, 180, 90), 'EPSG:4326')
        defaults.update(
            dict(
                srid='EPSG:4326',
                bbox_polygon=instance.bbox_polygon,
                ll_bbox_polygon=instance.ll_bbox_polygon
            )
        )
    if instance.ll_bbox_polygon is None:
        instance.set_bounds_from_bbox(
            instance.bbox_polygon,
            instance.srid or instance.bbox_polygon.srid
        )
        defaults.update(
            dict(
                srid=instance.srid,
                bbox_polygon=instance.bbox_polygon,
                ll_bbox_polygon=instance.ll_bbox_polygon
            )
        )

    ResourceBase.objects.filter(id=instance.id).update(
        **defaults
    )

    try:
        if not instance.regions or instance.regions.count() == 0:
            srid1, wkt1 = instance.geographic_bounding_box.split(";")
            srid1 = re.findall(r'\d+', srid1)

            poly1 = GEOSGeometry(wkt1, srid=int(srid1[0]))
            poly1.transform(4326)

            queryset = Region.objects.all().order_by('name')
            global_regions = []
            regions_to_add = []
            for region in queryset:
                try:
                    srid2, wkt2 = region.geographic_bounding_box.split(";")
                    srid2 = re.findall(r'\d+', srid2)

                    poly2 = GEOSGeometry(wkt2, srid=int(srid2[0]))
                    poly2.transform(4326)

                    if poly2.intersection(poly1):
                        regions_to_add.append(region)
                    if region.level == 0 and region.parent is None:
                        global_regions.append(region)
                except Exception:
                    tb = traceback.format_exc()
                    if tb:
                        logger.debug(tb)
            if regions_to_add or global_regions:
                if regions_to_add and len(
                        regions_to_add) > 0 and len(regions_to_add) <= 30:
                    instance.regions.add(*regions_to_add)
                else:
                    instance.regions.add(*global_regions)
    except Exception:
        tb = traceback.format_exc()
        if tb:
            logger.debug(tb)
    finally:
        # refresh catalogue metadata records
        from ..catalogue.models import catalogue_post_save
        catalogue_post_save(instance=instance, sender=instance.__class__)


def resourcebase_post_save(instance, *args, **kwargs):
    """
    Used to fill any additional fields after the save.
    Has to be called by the children
    """
    if instance:
        if hasattr(instance, 'abstract') and not getattr(instance, 'abstract', None):
            instance.abstract = _('No abstract provided')
        if hasattr(instance, 'title') and not getattr(instance, 'title', None) or getattr(instance, 'title', '') == '':
            if isinstance(instance, Document) and instance.files:
                instance.title = os.path.basename(instance.files[0])
            if hasattr(instance, 'name') and getattr(instance, 'name', None):
                instance.title = instance.name
        if hasattr(instance, 'alternate') and not getattr(instance, 'alternate', None) or getattr(instance, 'alternate', '') == '':
            instance.alternate = get_alternate_name(instance)

        if isinstance(instance, Document):
            document_post_save(instance, *args, **kwargs)
        if isinstance(instance, Dataset):
            dataset_post_save(instance, *args, **kwargs)

        metadata_post_save(instance, *args, **kwargs)
