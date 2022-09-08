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
import os
import json
import decimal
import logging
import warnings
import traceback
from django.urls import reverse

from owslib.wfs import WebFeatureService
import xml.etree.ElementTree as ET

from django.conf import settings

from django.db.models import F
from django.http import Http404, JsonResponse
from django.contrib import messages
from django.shortcuts import render
from django.utils.html import escape
from django.forms.utils import ErrorList
from django.contrib.auth import get_user_model
from django.template.loader import get_template
from django.utils.translation import ugettext as _
from django.core.exceptions import PermissionDenied
from django.forms.models import inlineformset_factory
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_http_methods

from geonode import geoserver
from geonode.layers.metadata import parse_metadata
from geonode.proxy.views import fetch_response_headers
from geonode.resource.manager import resource_manager
from geonode.geoserver.helpers import set_dataset_style, wps_format_is_supported
from geonode.resource.utils import update_resource

from geonode.base.auth import get_or_create_token
from geonode.base.forms import CategoryForm, TKeywordForm, ThesaurusAvailableForm
from geonode.base.views import batch_modify
from geonode.base.models import (
    Thesaurus,
    TopicCategory)
from geonode.base.enumerations import CHARSETS
from geonode.decorators import check_keyword_write_perms
from geonode.layers.forms import (
    DatasetForm,
    DatasetTimeSerieForm,
    LayerAttributeForm,
    NewLayerUploadForm)
from geonode.layers.models import (
    Dataset,
    Attribute)
from geonode.layers.utils import (
    is_sld_upload_only, is_xml_upload_only,
    validate_input_source)
from geonode.services.models import Service
from geonode.base import register_event
from geonode.monitoring.models import EventType
from geonode.groups.models import GroupProfile
from geonode.security.utils import (
    get_user_visible_groups,
    AdvancedSecurityWorkflowManager)
from geonode.people.forms import ProfileForm
from geonode.utils import HttpClient, check_ogc_backend, llbbox_to_mercator, resolve_object, mkdtemp
from geonode.geoserver.helpers import (
    ogc_server_settings,
    select_relevant_files,
    write_uploaded_files_to_disk)
from geonode.geoserver.security import set_geowebcache_invalidate_cache

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    from geonode.geoserver.helpers import gs_catalog

CONTEXT_LOG_FILE = ogc_server_settings.LOG_FILE

logger = logging.getLogger("geonode.layers.views")

DEFAULT_SEARCH_BATCH_SIZE = 10
MAX_SEARCH_BATCH_SIZE = 25
GENERIC_UPLOAD_ERROR = _("There was an error while attempting to upload your data. \
Please try again, or contact and administrator if the problem continues.")

METADATA_UPLOADED_PRESERVE_ERROR = _("Note: this dataset's orginal metadata was \
populated and preserved by importing a metadata XML file. This metadata cannot be edited.")

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this dataset")
_PERMISSION_MSG_GENERIC = _('You do not have permissions for this dataset.')
_PERMISSION_MSG_MODIFY = _("You are not permitted to modify this dataset")
_PERMISSION_MSG_METADATA = _("You are not permitted to modify this dataset's metadata")
_PERMISSION_MSG_VIEW = _("You are not permitted to view this dataset")


def log_snippet(log_file):
    if not log_file or not os.path.isfile(log_file):
        return f"No log file at {log_file}"

    with open(log_file) as f:
        f.seek(0, 2)  # Seek @ EOF
        fsize = f.tell()  # Get Size
        f.seek(max(fsize - 10024, 0), 0)  # Set pos @ last n chars
        return f.read()


def _resolve_dataset(request, alternate, permission='base.view_resourcebase', msg=_PERMISSION_MSG_GENERIC, **kwargs):
    """
    Resolve the layer by the provided typename (which may include service name) and check the optional permission.
    """
    service_typename = alternate.split(":", 1)
    if Service.objects.filter(name=service_typename[0]).count() == 1:
        query = {
            'alternate': service_typename[1],
            'remote_service': Service.objects.filter(name=service_typename[0]).get()
        }
        return resolve_object(
            request,
            Dataset,
            query,
            permission=permission,
            permission_msg=msg,
            **kwargs)
    else:
        if len(service_typename) > 1 and ':' in service_typename[1]:
            if service_typename[0]:
                query = {
                    'store': service_typename[0],
                    'alternate': service_typename[1]
                }
            else:
                query = {
                    'alternate': service_typename[1]
                }
        else:
            query = {'alternate': alternate}
        test_query = Dataset.objects.filter(**query)
        if test_query.count() > 1 and test_query.exclude(subtype='remote').count() == 1:
            query = {
                'id': test_query.exclude(subtype='remote').last().id
            }
        elif test_query.count() > 1:
            query = {
                'id': test_query.last().id
            }
        return resolve_object(request,
                              Dataset,
                              query,
                              permission=permission,
                              permission_msg=msg,
                              **kwargs)


# Basic Dataset Views #

@login_required
@require_http_methods(["POST"])
def dataset_upload(request):
    if is_xml_upload_only(request):
        return dataset_upload_metadata(request)
    elif is_sld_upload_only(request):
        return dataset_style_upload(request)
    out = {"errormsgs": "Please, execute a valid upload request"}
    return HttpResponse(
        json.dumps(out),
        content_type='application/json',
        status=500)


def dataset_upload_metadata(request):
    out = {}
    errormsgs = []

    form = NewLayerUploadForm(request.POST, request.FILES)

    if form.is_valid():
        tempdir = mkdtemp()
        relevant_files = select_relevant_files(
            ['xml'],
            iter(request.FILES.values())
        )
        logger.debug(f"relevant_files: {relevant_files}")
        write_uploaded_files_to_disk(tempdir, relevant_files)
        base_file = os.path.join(tempdir, form.cleaned_data["base_file"].name)
        layer = _resolve_dataset(
            request,
            form.cleaned_data.get('dataset_title'),
            'base.change_resourcebase',
            _PERMISSION_MSG_MODIFY)
        if layer:
            dataset_uuid, vals, regions, keywords, _ = parse_metadata(
                open(base_file).read())
            if dataset_uuid and layer.uuid != dataset_uuid:
                out['success'] = False
                out['errors'] = "The UUID identifier from the XML Metadata, is different from the one saved"
                return HttpResponse(
                    json.dumps(out),
                    content_type='application/json',
                    status=404)
            updated_dataset = update_resource(layer, base_file, regions, keywords, vals)
            updated_dataset.save()
            out['status'] = ['finished']
            out['url'] = updated_dataset.get_absolute_url()
            out['bbox'] = updated_dataset.bbox_string
            out['crs'] = {
                'type': 'name',
                'properties': updated_dataset.srid
            }
            out['ogc_backend'] = settings.OGC_SERVER['default']['BACKEND']
            if hasattr(updated_dataset, 'upload_session'):
                upload_session = updated_dataset.upload_session
                upload_session.processed = True
                upload_session.save()
            status_code = 200
            out['success'] = True
            return HttpResponse(
                json.dumps(out),
                content_type='application/json',
                status=status_code)
        else:
            out['success'] = False
            out['errors'] = "Dataset selected does not exists"
            status_code = 404
        return HttpResponse(
            json.dumps(out),
            content_type='application/json',
            status=status_code)
    else:
        for e in form.errors.values():
            errormsgs.extend([escape(v) for v in e])
        out['errors'] = form.errors
        out['errormsgs'] = errormsgs

    return HttpResponse(
        json.dumps(out),
        content_type='application/json',
        status=500)


def dataset_style_upload(request):
    out = {}
    errormsgs = []

    form = NewLayerUploadForm(request.POST, request.FILES)

    if form.is_valid():
        status_code = 200
        try:
            data = form.cleaned_data
            out = {
                'success': True,
                'style': data.get('dataset_title'),
            }

            layer = _resolve_dataset(
                request,
                data.get('dataset_title'),
                'base.change_resourcebase',
                _PERMISSION_MSG_MODIFY)

            if layer:
                sld = request.FILES['sld_file'].read()

                set_dataset_style(layer, data.get('dataset_title'), sld)
                out['url'] = layer.get_absolute_url()
                out['bbox'] = layer.bbox_string
                out['crs'] = {
                    'type': 'name',
                    'properties': layer.srid
                }
                out['ogc_backend'] = settings.OGC_SERVER['default']['BACKEND']
                out['status'] = ['finished']
            else:
                out['success'] = False
                out['errors'] = "Dataset selected does not exists"
                status_code = 404
        except Exception as e:
            status_code = 500
            out['success'] = False
            out['errors'] = str(e.args[0])

        return HttpResponse(
            json.dumps(out),
            content_type='application/json',
            status=status_code)
    else:
        for e in form.errors.values():
            errormsgs.extend([escape(v) for v in e])
        out['errors'] = errormsgs
        out['errormsgs'] = errormsgs

    return HttpResponse(
        json.dumps(out),
        content_type='application/json',
        status=500)


# Loads the data using the OWS lib when the "Do you want to filter it"
# button is clicked.
def load_dataset_data(request):
    context_dict = {}
    data_dict = json.loads(request.POST.get('json_data'))
    layername = data_dict['dataset_name']
    filtered_attributes = ''
    if not isinstance(data_dict['filtered_attributes'], str):
        filtered_attributes = [x for x in data_dict['filtered_attributes'] if '/load_dataset_data' not in x]
    name = layername if ':' not in layername else layername.split(':')[1]
    location = f"{(settings.OGC_SERVER['default']['LOCATION'])}wms"
    headers = {}
    if request and 'access_token' in request.session:
        access_token = request.session['access_token']
        headers['Authorization'] = f'Bearer {access_token}'

    try:
        wfs = WebFeatureService(
            location,
            version='1.1.0',
            headers=headers
        )
        response = wfs.getfeature(
            typename=name,
            propertyname=filtered_attributes,
            outputFormat='application/json')
        x = response.read()
        x = json.loads(x)
        features_response = json.dumps(x)
        decoded = json.loads(features_response)
        decoded_features = decoded['features']
        properties = {}
        for key in decoded_features[0]['properties']:
            properties[key] = []

        # loop the dictionary based on the values on the list and add the properties
        # in the dictionary (if doesn't exist) together with the value
        from collections.abc import Iterable
        for i in range(len(decoded_features)):
            for key, value in decoded_features[i]['properties'].items():
                if value != '' and isinstance(value, (str, int, float)) and (
                        (isinstance(value, Iterable) and '/load_dataset_data' not in value) or value):
                    properties[key].append(value)

        for key in properties:
            properties[key] = list(set(properties[key]))
            properties[key].sort()

        context_dict["feature_properties"] = properties
    except Exception:
        traceback.print_exc()
        logger.error("Possible error with OWSLib.")
    return HttpResponse(json.dumps(context_dict),
                        content_type="application/json")


def dataset_feature_catalogue(
        request,
        layername,
        template='../../catalogue/templates/catalogue/feature_catalogue.xml'):
    try:
        layer = _resolve_dataset(request, layername)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not layer:
        raise Http404(_("Not found"))

    if layer.subtype != 'vector':
        out = {
            'success': False,
            'errors': 'layer is not a feature type'
        }
        return HttpResponse(
            json.dumps(out),
            content_type='application/json',
            status=400)

    attributes = []

    for attrset in layer.attribute_set.order_by('display_order'):
        attr = {
            'name': attrset.attribute,
            'type': attrset.attribute_type
        }
        attributes.append(attr)

    context_dict = {
        'dataset': layer,
        'attributes': attributes,
        'metadata': settings.PYCSW['CONFIGURATION']['metadata:main']
    }
    register_event(request, 'view', layer)
    return render(
        request,
        template,
        context=context_dict,
        content_type='application/xml')


@login_required
@check_keyword_write_perms
def dataset_metadata(
        request,
        layername,
        template='datasets/dataset_metadata.html',
        ajax=True):
    try:
        layer = _resolve_dataset(
            request,
            layername,
            'base.change_resourcebase_metadata',
            _PERMISSION_MSG_METADATA)
    except PermissionDenied as e:
        return HttpResponse(Exception(_("Not allowed"), e), status=403)
    except Exception as e:
        raise Http404(Exception(_("Not found"), e))
    if not layer:
        raise Http404(_("Not found"))

    dataset_attribute_set = inlineformset_factory(
        Dataset,
        Attribute,
        extra=0,
        form=LayerAttributeForm,
    )
    current_keywords = [keyword.name for keyword in layer.keywords.all()]
    topic_category = layer.category

    topic_thesaurus = layer.tkeywords.all()
    # Add metadata_author or poc if missing
    layer.add_missing_metadata_author_or_poc()

    poc = layer.poc
    metadata_author = layer.metadata_author

    # assert False, str(dataset_bbox)
    config = layer.attribute_config()

    # Add required parameters for GXP lazy-loading
    dataset_bbox = layer.bbox
    bbox = [float(coord) for coord in list(dataset_bbox[0:4])]
    if hasattr(layer, 'srid'):
        config['crs'] = {
            'type': 'name',
            'properties': layer.srid
        }
    config["srs"] = getattr(settings, 'DEFAULT_MAP_CRS', 'EPSG:3857')
    config["bbox"] = bbox if config["srs"] != 'EPSG:3857' \
        else llbbox_to_mercator([float(coord) for coord in bbox])
    config["title"] = layer.title
    config["queryable"] = True

    # Update count for popularity ranking,
    # but do not includes admins or resource owners
    if request.user != layer.owner and not request.user.is_superuser:
        Dataset.objects.filter(
            id=layer.id).update(popular_count=F('popular_count') + 1)

    if request.method == "POST":
        if layer.metadata_uploaded_preserve:  # layer metadata cannot be edited
            out = {
                'success': False,
                'errors': METADATA_UPLOADED_PRESERVE_ERROR
            }
            return HttpResponse(
                json.dumps(out),
                content_type='application/json',
                status=400)

        thumbnail_url = layer.thumbnail_url
        dataset_form = DatasetForm(request.POST, instance=layer, prefix="resource", user=request.user)

        if not dataset_form.is_valid():
            logger.error(f"Dataset Metadata form is not valid: {dataset_form.errors}")
            out = {
                'success': False,
                'errors': [f"{x}: {y[0].messages[0]}" for x, y in dataset_form.errors.as_data().items()]
            }
            return HttpResponse(
                json.dumps(out),
                content_type='application/json',
                status=400)
        if not layer.thumbnail_url:
            layer.thumbnail_url = thumbnail_url
        attribute_form = dataset_attribute_set(
            request.POST,
            instance=layer,
            prefix="dataset_attribute_set",
            queryset=Attribute.objects.order_by('display_order'))
        if not attribute_form.is_valid():
            logger.error(f"Dataset Attributes form is not valid: {attribute_form.errors}")
            out = {
                'success': False,
                "errors": [re.sub(re.compile('<.*?>'), '', str(err)) for err in attribute_form.errors]
            }
            return HttpResponse(
                json.dumps(out),
                content_type='application/json',
                status=400)
        category_form = CategoryForm(request.POST, prefix="category_choice_field", initial=int(
            request.POST["category_choice_field"]) if "category_choice_field" in request.POST and
            request.POST["category_choice_field"] else None)
        if not category_form.is_valid():
            logger.error(f"Dataset Category form is not valid: {category_form.errors}")
            out = {
                'success': False,
                'errors': [
                    re.sub(re.compile('<.*?>'), '', str(err)) for err in category_form.errors]
            }
            return HttpResponse(
                json.dumps(out),
                content_type='application/json',
                status=400)
        if hasattr(settings, 'THESAURUS'):
            tkeywords_form = TKeywordForm(request.POST)
        else:
            tkeywords_form = ThesaurusAvailableForm(request.POST, prefix='tkeywords')
            #  set initial values for thesaurus form
        if not tkeywords_form.is_valid():
            logger.error(f"Dataset Thesauri Keywords form is not valid: {tkeywords_form.errors}")
            out = {
                'success': False,
                'errors': [
                    re.sub(re.compile('<.*?>'), '', str(err)) for err in tkeywords_form.errors]
            }
            return HttpResponse(
                json.dumps(out),
                content_type='application/json',
                status=400)

        timeseries_form = DatasetTimeSerieForm(request.POST, instance=layer, prefix='timeseries')
        if not timeseries_form.is_valid():
            out = {
                'success': False,
                'errors': [f"{x}: {y[0].messages[0]}" for x, y in timeseries_form.errors.as_data().items()]
            }
            logger.error(f"{out.get('errors')}")
            return HttpResponse(
                json.dumps(out),
                content_type='application/json',
                status=400)
    else:
        dataset_form = DatasetForm(instance=layer, prefix="resource", user=request.user)
        dataset_form.disable_keywords_widget_for_non_superuser(request.user)
        attribute_form = dataset_attribute_set(
            instance=layer,
            prefix="dataset_attribute_set",
            queryset=Attribute.objects.order_by('display_order'))
        category_form = CategoryForm(
            prefix="category_choice_field",
            initial=topic_category.id if topic_category else None)

        gs_layer = gs_catalog.get_layer(name=layer.name)
        initial = {}
        if gs_layer is not None and layer.has_time:
            gs_time_info = gs_layer.resource.metadata.get("time")
            if gs_time_info.enabled:
                _attr = layer.attributes.filter(attribute=gs_time_info.attribute).first()
                initial["attribute"] = _attr.pk if _attr else None
                if gs_time_info.end_attribute is not None:
                    end_attr = layer.attributes.filter(attribute=gs_time_info.end_attribute).first()
                    initial["end_attribute"] = end_attr.pk if end_attr else None
                initial["presentation"] = gs_time_info.presentation
                lookup_value = sorted(list(gs_time_info._lookup), key=lambda x: x[1], reverse=True)
                if gs_time_info.resolution is not None:
                    res = gs_time_info.resolution // 1000
                    for el in lookup_value:
                        if res % el[1] == 0:
                            initial["precision_value"] = res // el[1]
                            initial["precision_step"] = el[0]
                            break
                else:
                    initial["precision_value"] = gs_time_info.resolution
                    initial["precision_step"] = "seconds"

        timeseries_form = DatasetTimeSerieForm(
            instance=layer,
            prefix="timeseries",
            initial=initial
        )
        timeseries_form.fields.get('attribute').queryset = layer.attributes.filter(attribute_type__in=['xsd:dateTime'])
        timeseries_form.fields.get('end_attribute').queryset = layer.attributes.filter(attribute_type__in=['xsd:dateTime'])

        # Create THESAURUS widgets
        lang = settings.THESAURUS_DEFAULT_LANG if hasattr(settings, 'THESAURUS_DEFAULT_LANG') else 'en'
        if hasattr(settings, 'THESAURUS') and settings.THESAURUS:
            warnings.warn('The settings for Thesaurus has been moved to Model, \
            this feature will be removed in next releases', DeprecationWarning)
            dataset_tkeywords = layer.tkeywords.all()
            tkeywords_list = ''
            if dataset_tkeywords and len(dataset_tkeywords) > 0:
                tkeywords_ids = dataset_tkeywords.values_list('id', flat=True)
                if hasattr(settings, 'THESAURUS') and settings.THESAURUS:
                    el = settings.THESAURUS
                    thesaurus_name = el['name']
                    try:
                        t = Thesaurus.objects.get(identifier=thesaurus_name)
                        for tk in t.thesaurus.filter(pk__in=tkeywords_ids):
                            tkl = tk.keyword.filter(lang=lang)
                            if len(tkl) > 0:
                                tkl_ids = ",".join(
                                    map(str, tkl.values_list('id', flat=True)))
                                tkeywords_list += f",{tkl_ids}" if len(
                                    tkeywords_list) > 0 else tkl_ids
                    except Exception:
                        tb = traceback.format_exc()
                        logger.error(tb)
            tkeywords_form = TKeywordForm(instance=layer)
        else:
            tkeywords_form = ThesaurusAvailableForm(prefix='tkeywords')
            #  set initial values for thesaurus form
            for tid in tkeywords_form.fields:
                values = []
                values = [keyword.id for keyword in topic_thesaurus if int(tid) == keyword.thesaurus.id]
                tkeywords_form.fields[tid].initial = values

    if request.method == "POST" and dataset_form.is_valid() and attribute_form.is_valid(
    ) and category_form.is_valid() and tkeywords_form.is_valid() and timeseries_form.is_valid():
        new_poc = dataset_form.cleaned_data['poc']
        new_author = dataset_form.cleaned_data['metadata_author']

        if new_poc is None:
            if poc is None:
                poc_form = ProfileForm(
                    request.POST,
                    prefix="poc",
                    instance=poc)
            else:
                poc_form = ProfileForm(request.POST, prefix="poc")
            if poc_form.is_valid():
                if len(poc_form.cleaned_data['profile']) == 0:
                    # FIXME use form.add_error in django > 1.7
                    errors = poc_form._errors.setdefault(
                        'profile', ErrorList())
                    errors.append(
                        _('You must set a point of contact for this resource'))
                    poc = None
            if poc_form.has_changed and poc_form.is_valid():
                new_poc = poc_form.save()

        if new_author is None:
            if metadata_author is None:
                author_form = ProfileForm(request.POST, prefix="author",
                                          instance=metadata_author)
            else:
                author_form = ProfileForm(request.POST, prefix="author")
            if author_form.is_valid():
                if len(author_form.cleaned_data['profile']) == 0:
                    # FIXME use form.add_error in django > 1.7
                    errors = author_form._errors.setdefault(
                        'profile', ErrorList())
                    errors.append(
                        _('You must set an author for this resource'))
                    metadata_author = None
            if author_form.has_changed and author_form.is_valid():
                new_author = author_form.save()

        new_category = None
        if category_form and 'category_choice_field' in category_form.cleaned_data and\
                category_form.cleaned_data['category_choice_field']:
            new_category = TopicCategory.objects.get(
                id=int(category_form.cleaned_data['category_choice_field']))

        for form in attribute_form.cleaned_data:
            la = Attribute.objects.get(id=int(form['id'].id))
            la.description = form["description"]
            la.attribute_label = form["attribute_label"]
            la.visible = form["visible"]
            la.display_order = form["display_order"]
            la.featureinfo_type = form["featureinfo_type"]
            la.save()

        if new_poc is not None or new_author is not None:
            if new_poc is not None:
                layer.poc = new_poc
            if new_author is not None:
                layer.metadata_author = new_author

        new_keywords = current_keywords if request.keyword_readonly else dataset_form.cleaned_data['keywords']
        new_regions = [x.strip() for x in dataset_form.cleaned_data['regions']]

        layer.keywords.clear()
        if new_keywords:
            layer.keywords.add(*new_keywords)
        layer.regions.clear()
        if new_regions:
            layer.regions.add(*new_regions)
        layer.category = new_category

        from geonode.upload.models import Upload

        up_sessions = Upload.objects.filter(resource_id=layer.resourcebase_ptr_id)
        if up_sessions.exists() and up_sessions[0].user != layer.owner:
            up_sessions.update(user=layer.owner)

        register_event(request, EventType.EVENT_CHANGE_METADATA, layer)
        if not ajax:
            return HttpResponseRedirect(layer.get_absolute_url())

        message = layer.alternate

        try:
            if not tkeywords_form.is_valid():
                return HttpResponse(json.dumps({'message': "Invalid thesaurus keywords"}, status_code=400))

            thesaurus_setting = getattr(settings, 'THESAURUS', None)
            if thesaurus_setting:
                tkeywords_data = tkeywords_form.cleaned_data['tkeywords']
                tkeywords_data = tkeywords_data.filter(
                    thesaurus__identifier=thesaurus_setting['name']
                )
                layer.tkeywords.set(tkeywords_data)
            elif Thesaurus.objects.all().exists():
                fields = tkeywords_form.cleaned_data
                layer.tkeywords.set(tkeywords_form.cleanx(fields))

        except Exception:
            tb = traceback.format_exc()
            logger.error(tb)

        vals = {}
        if 'group' in dataset_form.changed_data:
            vals['group'] = dataset_form.cleaned_data.get('group')
        if any([x in dataset_form.changed_data for x in ['is_approved', 'is_published']]):
            vals['is_approved'] = dataset_form.cleaned_data.get('is_approved', layer.is_approved)
            vals['is_published'] = dataset_form.cleaned_data.get('is_published', layer.is_published)

        layer.has_time = dataset_form.cleaned_data.get('has_time', layer.has_time)

        if layer.is_vector() and timeseries_form.cleaned_data and ('has_time' in dataset_form.changed_data or timeseries_form.changed_data):
            ts = timeseries_form.cleaned_data
            end_attr = layer.attributes.get(pk=ts.get("end_attribute")).attribute if ts.get("end_attribute") else None
            start_attr = layer.attributes.get(pk=ts.get("attribute")).attribute if ts.get("attribute") else None
            resource_manager.exec(
                'set_time_info',
                None,
                instance=layer,
                time_info={
                    "attribute": start_attr,
                    "end_attribute": end_attr,
                    "presentation": ts.get('presentation', None),
                    "precision_value": ts.get('precision_value', None),
                    "precision_step": ts.get('precision_step', None),
                    "enabled": dataset_form.cleaned_data.get('has_time', False)
                }
            )

        resource_manager.update(
            layer.uuid,
            instance=layer,
            notify=True,
            vals=vals,
            extra_metadata=json.loads(dataset_form.cleaned_data['extra_metadata'])
        )

        return HttpResponse(json.dumps({'message': message}))

    if not AdvancedSecurityWorkflowManager.is_allowed_to_publish(request.user, layer):
        dataset_form.fields['is_published'].widget.attrs.update({'disabled': 'true'})
    if not AdvancedSecurityWorkflowManager.is_allowed_to_approve(request.user, layer):
        dataset_form.fields['is_approved'].widget.attrs.update({'disabled': 'true'})

    if poc is not None:
        dataset_form.fields['poc'].initial = poc.id
        poc_form = ProfileForm(prefix="poc")
        poc_form.hidden = True
    else:
        poc_form = ProfileForm(prefix="poc")
        poc_form.hidden = False

    if metadata_author is not None:
        dataset_form.fields['metadata_author'].initial = metadata_author.id
        author_form = ProfileForm(prefix="author")
        author_form.hidden = True
    else:
        author_form = ProfileForm(prefix="author")
        author_form.hidden = False

    metadata_author_groups = get_user_visible_groups(request.user)

    register_event(request, 'view_metadata', layer)
    return render(request, template, context={
        "resource": layer,
        "dataset": layer,
        "dataset_form": dataset_form,
        "poc_form": poc_form,
        "author_form": author_form,
        "attribute_form": attribute_form,
        "timeseries_form": timeseries_form,
        "category_form": category_form,
        "tkeywords_form": tkeywords_form,
        "preview": getattr(settings, 'GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY', 'mapstore'),
        "crs": getattr(settings, 'DEFAULT_MAP_CRS', 'EPSG:3857'),
        "metadataxsl": getattr(settings, 'GEONODE_CATALOGUE_METADATA_XSL', True),
        "freetext_readonly": getattr(
            settings,
            'FREETEXT_KEYWORDS_READONLY',
            False),
        "metadata_author_groups": metadata_author_groups,
        "TOPICCATEGORY_MANDATORY": getattr(settings, 'TOPICCATEGORY_MANDATORY', False),
        "GROUP_MANDATORY_RESOURCES": getattr(settings, 'GROUP_MANDATORY_RESOURCES', False),
        "UI_MANDATORY_FIELDS": list(
            set(getattr(settings, 'UI_DEFAULT_MANDATORY_FIELDS', []))
            |
            set(getattr(settings, 'UI_REQUIRED_FIELDS', []))
        )
    })


@login_required
def dataset_metadata_advanced(request, layername):
    return dataset_metadata(
        request,
        layername,
        template='datasets/dataset_metadata_advanced.html')


@csrf_exempt
def dataset_download(request, layername):
    try:
        dataset = _resolve_dataset(
            request,
            layername,
            'base.download_resourcebase',
            _PERMISSION_MSG_GENERIC)
    except Exception as e:
        raise Http404(Exception(_("Not found"), e))

    if not settings.USE_GEOSERVER:
        # if GeoServer is not used, we redirect to the proxy download
        return HttpResponseRedirect(reverse('download', args=[dataset.id]))

    download_format = request.GET.get('export_format')

    if download_format and not wps_format_is_supported(download_format, dataset.subtype):
        logger.error("The format provided is not valid for the selected resource")
        return JsonResponse({"error": "The format provided is not valid for the selected resource"}, status=500)

    _format = 'application/zip' if dataset.is_vector() else 'image/tiff'
    # getting default payload
    tpl = get_template("geoserver/dataset_download.xml")
    ctx = {
        "alternate": dataset.alternate,
        "download_format": download_format or _format
    }
    # applying context for the payload
    payload = tpl.render(ctx)

    # init of Client
    client = HttpClient()

    headers = {
        "Content-type": "application/xml",
        "Accept": "application/xml"
    }

    # defining the URL needed fr the download
    url = f"{settings.OGC_SERVER['default']['LOCATION']}ows?service=WPS&version=1.0.0&REQUEST=Execute"
    if not request.user.is_anonymous:
        # define access token for the user
        access_token = get_or_create_token(request.user)
        url += f"&access_token={access_token}"

    # request to geoserver
    response, content = client.request(
        url=url,
        data=payload,
        method="post",
        headers=headers
    )

    if response.status_code != 200:
        logger.error(f"Download dataset exception: error during call with GeoServer: {response.content}")
        return JsonResponse(
            {"error": f"Download dataset exception: error during call with GeoServer: {response.content}"},
            status=500
        )

    # error handling
    namespaces = {"ows": "http://www.opengis.net/ows/1.1", "wps": "http://www.opengis.net/wps/1.0.0"}
    response_type = response.headers.get('Content-Type')
    if response_type == 'text/xml':
        # parsing XML for get exception
        content = ET.fromstring(response.text)
        exc = content.find('*//ows:Exception', namespaces=namespaces) or content.find('ows:Exception', namespaces=namespaces)
        if exc:
            exc_text = exc.find('ows:ExceptionText', namespaces=namespaces)
            logger.error(f"{exc.attrib.get('exceptionCode')} {exc_text.text}")
            return JsonResponse({"error": f"{exc.attrib.get('exceptionCode')}: {exc_text.text}"}, status=500)

    return_response = fetch_response_headers(
        HttpResponse(
            content=response.content,
            status=response.status_code,
            content_type=download_format
        ), response.headers)
    return_response.headers['Content-Type'] = download_format or _format
    return return_response


@login_required
def dataset_replace(request, layername, template='datasets/dataset_replace.html'):
    return dataset_append_replace_view(request, layername, template, action_type='replace')


@login_required
def dataset_append(request, layername, template='datasets/dataset_append.html'):
    return dataset_append_replace_view(request, layername, template, action_type='append')


def dataset_append_replace_view(request, layername, template, action_type):
    try:
        dataset = _resolve_dataset(
            request,
            layername,
            'base.change_resourcebase',
            _PERMISSION_MSG_MODIFY)
    except PermissionDenied:
        return HttpResponse("Not allowed", status=403)
    except Exception:
        raise Http404("Not found")
    if not dataset:
        raise Http404("Not found")

    if request.method == 'GET':
        ctx = {
            'charsets': CHARSETS,
            'resource': dataset,
            'is_featuretype': dataset.is_vector(),
            'is_dataset': True,
        }
        return render(request, template, context=ctx)
    elif request.method == 'POST':
        from geonode.upload.forms import LayerUploadForm as UploadForm
        form = UploadForm(request.POST, request.FILES, user=request.user)
        out = {}
        if form.is_valid():
            storage_manager = form.cleaned_data.get('storage_manager')
            try:
                store_spatial_files = form.cleaned_data.get('store_spatial_files', True)

                file_paths = storage_manager.get_retrieved_paths()
                base_file = file_paths.get('base_file')
                files = {_file.split(".")[1]: _file for _file in file_paths.values()}

                resource_is_valid = validate_input_source(
                    layer=dataset, filename=base_file, files=files, action_type=action_type
                )
                out = {}
                if resource_is_valid:
                    xml_file = file_paths.pop('xml_file', None)
                    sld_file = file_paths.pop('sld_file', None)

                    call_kwargs = {
                        "instance": dataset,
                        "vals": {'files': list(files.values()), 'user': request.user},
                        "store_spatial_files": store_spatial_files,
                        "xml_file": xml_file,
                        "metadata_uploaded": True if xml_file is not None else False,
                        "sld_file": sld_file,
                        "sld_uploaded": True if sld_file is not None else False
                    }

                    getattr(resource_manager, action_type)(**call_kwargs)

                    out['success'] = True
                    out['url'] = dataset.get_absolute_url()
                    #  invalidating resource chache
                    set_geowebcache_invalidate_cache(dataset.typename)
            except Exception as e:
                logger.exception(e)
                raise e
            finally:
                if not store_spatial_files:
                    storage_manager.delete_retrieved_paths(force=True)
        else:
            errormsgs = []
            for e in form.errors.values():
                errormsgs.append([escape(v) for v in e])
            out['errors'] = form.errors
            out['errormsgs'] = errormsgs

        if out['success']:
            status_code = 200
            register_event(request, 'change', dataset)
        else:
            status_code = 400

        return HttpResponse(
            json.dumps(out),
            content_type='application/json',
            status=status_code)


@login_required
def dataset_granule_remove(
        request,
        granule_id,
        layername,
        template='datasets/dataset_granule_remove.html'):
    try:
        layer = _resolve_dataset(
            request,
            layername,
            'base.delete_resourcebase',
            _PERMISSION_MSG_DELETE)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not layer:
        raise Http404(_("Not found"))

    if (request.method == 'GET'):
        return render(request, template, context={
            "granule_id": granule_id,
            "dataset": layer
        })
    if (request.method == 'POST'):
        try:
            cat = gs_catalog
            cat._cache.clear()
            store = cat.get_store(layer.name)
            coverages = cat.mosaic_coverages(store)
            cat.mosaic_delete_granule(
                coverages['coverages']['coverage'][0]['name'], store, granule_id)
        except Exception as e:
            traceback.print_exc()
            message = f'{_("Unable to delete layer")}: {layer.alternate}.'
            if 'referenced by layer group' in getattr(e, 'message', ''):
                message = _(
                    'This dataset is a member of a layer group, you must remove the dataset from the group '
                    'before deleting.')

            messages.error(request, message)
            return render(
                request, template, context={"layer": layer})
        return HttpResponseRedirect(layer.get_absolute_url())
    else:
        return HttpResponse("Not allowed", status=403)


def get_dataset(request, layername):
    """Get Dataset object as JSON"""

    # Function to treat Decimal in json.dumps.
    # http://stackoverflow.com/a/16957370/1198772
    def decimal_default(obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        raise TypeError
    logger.debug('Call get layer')
    if request.method == 'GET':
        try:
            dataset_obj = _resolve_dataset(request, layername)
        except PermissionDenied:
            return HttpResponse(_("Not allowed"), status=403)
        except Exception:
            raise Http404(_("Not found"))
        if not dataset_obj:
            raise Http404(_("Not found"))

        logger.debug(layername)
        response = {
            'typename': layername,
            'name': dataset_obj.name,
            'title': dataset_obj.title,
            'url': dataset_obj.get_tiles_url(),
            'bbox_string': dataset_obj.bbox_string,
            'bbox_x0': dataset_obj.bbox_helper.xmin,
            'bbox_x1': dataset_obj.bbox_helper.xmax,
            'bbox_y0': dataset_obj.bbox_helper.ymin,
            'bbox_y1': dataset_obj.bbox_helper.ymax,
        }
        return HttpResponse(
            json.dumps(
                response,
                ensure_ascii=False,
                default=decimal_default
            ),
            content_type='application/javascript')


def dataset_metadata_detail(
        request,
        layername,
        template='datasets/dataset_metadata_detail.html'):
    try:
        layer = _resolve_dataset(
            request,
            layername,
            'view_resourcebase',
            _PERMISSION_MSG_METADATA)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not layer:
        raise Http404(_("Not found"))

    group = None
    if layer.group:
        try:
            group = GroupProfile.objects.get(slug=layer.group.name)
        except GroupProfile.DoesNotExist:
            group = None
    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL

    register_event(request, 'view_metadata', layer)
    perms_list = list(
        layer.get_self_resource().get_user_perms(request.user)
        .union(layer.get_user_perms(request.user))
    )

    return render(request, template, context={
        "resource": layer,
        "perms_list": perms_list,
        "group": group,
        'SITEURL': site_url
    })


def dataset_metadata_upload(
        request,
        layername,
        template='datasets/dataset_metadata_upload.html'):
    try:
        layer = _resolve_dataset(
            request,
            layername,
            'base.change_resourcebase',
            _PERMISSION_MSG_METADATA)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not layer:
        raise Http404(_("Not found"))

    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
    return render(request, template, context={
        "resource": layer,
        "layer": layer,
        'SITEURL': site_url
    })


def dataset_sld_upload(
        request,
        layername,
        template='datasets/dataset_style_upload.html'):
    try:
        layer = _resolve_dataset(
            request,
            layername,
            'base.change_resourcebase',
            _PERMISSION_MSG_METADATA)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not layer:
        raise Http404(_("Not found"))

    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
    return render(request, template, context={
        "resource": layer,
        "dataset": layer,
        'SITEURL': site_url
    })


@xframe_options_exempt
def dataset_embed(
        request,
        layername):
    try:
        layer = _resolve_dataset(
            request,
            layername,
            'base.view_resourcebase',
            _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not layer:
        raise Http404(_("Not found"))

    # Update count for popularity ranking,
    # but do not includes admins or resource owners
    layer.view_count_up(request.user)

    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    context_dict = {
        'access_token': access_token,
        'resource': layer,
    }
    return TemplateResponse(request, 'datasets/dataset_embed.html', context=context_dict)


@login_required
def dataset_batch_metadata(request):
    return batch_modify(request, 'Dataset')


def dataset_view_counter(dataset_id, viewer):
    _l = Dataset.objects.get(id=dataset_id)
    _u = get_user_model().objects.get(username=viewer)
    _l.view_count_up(_u, do_local=True)
