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
import os
import logging
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from pycsw import server
from guardian.shortcuts import get_objects_for_user
from geonode.catalogue.backends.pycsw_local import CONFIGURATION
from geonode.base.models import ResourceBase
from geonode.layers.models import Dataset
from geonode.base.auth import get_or_create_token
from geonode.base.models import SpatialRepresentationType
from geonode.groups.models import GroupProfile
from geonode.utils import resolve_object
from django.db import connection
from django.core.exceptions import ObjectDoesNotExist
from geonode.people import Roles


@csrf_exempt
def csw_global_dispatch(request, dataset_filter=None, config_updater=None):
    """pycsw wrapper"""

    # this view should only operate if pycsw_local is the backend
    # else, redirect to the URL of the non-pycsw_local backend
    if settings.CATALOGUE["default"]["ENGINE"] != "geonode.catalogue.backends.pycsw_local":
        return HttpResponseRedirect(settings.CATALOGUE["default"]["URL"])

    mdict = dict(settings.PYCSW["CONFIGURATION"], **CONFIGURATION)
    mdict = config_updater(mdict) if config_updater else mdict

    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and access_token.is_expired():
            access_token = None

    absolute_uri = f"{request.build_absolute_uri()}"
    query_string = f"{request.META['QUERY_STRING']}"
    env = request.META.copy()

    if access_token and not access_token.is_expired():
        env.update({"access_token": access_token.token})
        if "access_token" not in query_string:
            absolute_uri = f"{absolute_uri}&access_token={access_token.token}"
            query_string = f"{query_string}&access_token={access_token.token}"

    env.update({"local.app_root": os.path.dirname(__file__), "REQUEST_URI": absolute_uri, "QUERY_STRING": query_string})

    # Save original filter before doing anything
    mdict_filter = mdict["repository"]["filter"]

    try:
        # Filter out Layers not accessible to the User
        authorized_ids = []
        if request.user:
            profiles = get_user_model().objects.filter(username=str(request.user))
        else:
            profiles = get_user_model().objects.filter(username="AnonymousUser")
        if profiles:
            authorized = list(get_objects_for_user(profiles[0], "base.view_resourcebase").values("id"))

            layers = ResourceBase.objects.filter(id__in=[d["id"] for d in authorized])

            if dataset_filter and layers:
                layers = dataset_filter(layers)

            if layers:
                authorized_ids = [d.id for d in layers]

        if len(authorized_ids) > 0:
            authorized_datasets = f"({', '.join(str(e) for e in authorized_ids)})"
            authorized_datasets_filter = f"id IN {authorized_datasets}"
            mdict["repository"]["filter"] += f" AND {authorized_datasets_filter}"
            if request.user and request.user.is_authenticated:
                mdict["repository"]["filter"] = f"({mdict['repository']['filter']}) OR ({authorized_datasets_filter})"
        else:
            authorized_datasets_filter = "id = -9999"
            mdict["repository"]["filter"] += f" AND {authorized_datasets_filter}"

        # Filter out Documents and Maps
        if "ALTERNATES_ONLY" in settings.CATALOGUE["default"] and settings.CATALOGUE["default"]["ALTERNATES_ONLY"]:
            mdict["repository"]["filter"] += " AND alternate IS NOT NULL"

        # Filter out Layers belonging to specific Groups
        is_admin = False
        if request.user:
            is_admin = request.user.is_superuser if request.user else False

        if not is_admin and settings.GROUP_PRIVATE_RESOURCES:
            groups_ids = []
            if request.user and request.user.is_authenticated:
                for group in request.user.groups.all():
                    groups_ids.append(group.id)
                group_list_all = []
                try:
                    group_list_all = request.user.group_list_all().values("group")
                except Exception:
                    pass
                for group in group_list_all:
                    if isinstance(group, dict):
                        if "group" in group:
                            groups_ids.append(group["group"])
                    else:
                        groups_ids.append(group.id)

            public_groups = GroupProfile.objects.exclude(access="private").values("group")
            for group in public_groups:
                if isinstance(group, dict):
                    if "group" in group:
                        groups_ids.append(group["group"])
                else:
                    groups_ids.append(group.id)

            if len(groups_ids) > 0:
                groups = f"({', '.join(str(e) for e in groups_ids)})"
                groups_filter = f"(group_id IS NULL OR group_id IN {groups})"
                mdict["repository"]["filter"] += f" AND {groups_filter}"
            else:
                groups_filter = "group_id IS NULL"
                mdict["repository"]["filter"] += f" AND {groups_filter}"

        csw = server.Csw(mdict, env, version="2.0.2")

        content = csw.dispatch_wsgi()

        # pycsw 2.0 has an API break:
        # - pycsw < 2.0: content = xml_response
        # - pycsw >= 2.0: content = [http_status_code, content]
        # deal with the API break

        if isinstance(content, list):  # pycsw 2.0+
            content = content[1]

    finally:
        # Restore original filter before doing anything
        mdict["repository"]["filter"] = mdict_filter

    return HttpResponse(content, content_type=csw.contenttype)


@csrf_exempt
def opensearch_dispatch(request):
    """OpenSearch wrapper"""

    ctx = {
        "shortname": settings.PYCSW["CONFIGURATION"]["metadata:main"]["identification_title"],
        "description": settings.PYCSW["CONFIGURATION"]["metadata:main"]["identification_abstract"],
        "developer": settings.PYCSW["CONFIGURATION"]["metadata:main"]["contact_name"],
        "contact": settings.PYCSW["CONFIGURATION"]["metadata:main"]["contact_email"],
        "attribution": settings.PYCSW["CONFIGURATION"]["metadata:main"]["provider_name"],
        "tags": settings.PYCSW["CONFIGURATION"]["metadata:main"]["identification_keywords"].replace(",", " "),
        "url": settings.SITEURL.rstrip("/") if settings.SITEURL.startswith("http") else settings.SITEURL,
    }

    return render(
        request,
        "catalogue/opensearch_description.xml",
        context=ctx,
        content_type="application/opensearchdescription+xml",
    )


# transforms a row sql query into a two dimension array
def dictfetchall(cursor):
    """Generate all rows from a cursor as a dict"""
    for row in cursor.fetchall():
        yield {col[0]: row for col in cursor.description}


# choose separators
def get_CSV_spec_char():
    return {"separator": ";", "carriage_return": "\r\n"}


# format value to unicode str without ';' char
def fst(value):
    chrs = get_CSV_spec_char()
    result = str(value)
    result = result.replace(chrs["separator"], ",").replace("\\n", " ").replace("\r\n", " ")
    return result


# from a resource object, build the corresponding metadata dict
# the aim is to handle the output format (csv, html or pdf) the same structure
def build_md_dict(resource):
    md_dict = {
        "r_uuid": {"label": "uuid", "value": resource.uuid},
        "r_title": {"label": "titre", "value": resource.title},
    }
    return md_dict


def get_keywords(resource):
    content = " "
    cursor = connection.cursor()
    cursor.execute(
        "SELECT a.*,b.* FROM taggit_taggeditem as a,taggit_tag" " as b WHERE a.object_id = %s AND a.tag_id=b.id",
        [resource.id],
    )
    for x in dictfetchall(cursor):
        content += f"{fst(x['name'])}, "
    return content[:-2]


# from a resource uuid, return a httpResponse
# containing the whole geonode metadata
@csrf_exempt
def csw_render_extra_format_txt(request, layeruuid, resname):
    """pycsw wrapper"""
    resource = ResourceBase.objects.get(uuid=layeruuid)
    chrs = get_CSV_spec_char()
    s = chrs["separator"]
    c = chrs["carriage_return"]
    sc = s + c
    content = f"Resource metadata{sc}"
    content += f"uuid{s}{fst(resource.uuid)}{sc}"
    content += f"title{s}{fst(resource.title)}{sc}"
    content += f"resource owner{s}{fst(resource.owner)}{sc}"
    content += f"date{s}{fst(resource.date)}{sc}"
    content += f"date type{s}{fst(resource.date_type)}{sc}"
    content += f"abstract{s}{fst(resource.abstract)}{sc}"
    content += f"edition{s}{fst(resource.edition)}{sc}"
    content += f"purpose{s}{fst(resource.purpose)}{sc}"
    content += f"maintenance frequency{s}{fst(resource.maintenance_frequency)}{sc}"

    try:
        sprt = SpatialRepresentationType.objects.get(id=resource.spatial_representation_type_id)
        content += f"identifier{s}{fst(sprt.identifier)}{sc}"
    except ObjectDoesNotExist:
        content += f"ObjectDoesNotExist{sc}"

    content += f"restriction code type{s}{fst(resource.restriction_code_type)}{sc}"
    content += f"constraints other {s}{fst(resource.constraints_other)}{sc}"
    content += f"license{s}{fst(resource.license)}{sc}"
    content += f"language{s}{fst(resource.language)}{sc}"
    content += f"temporal extent{sc}"
    content += f"temporal extent start{s}{fst(resource.temporal_extent_start)}{sc}"
    content += f"temporal extent end{s}{fst(resource.temporal_extent_end)}{sc}"
    content += f"supplemental information{s}{fst(resource.supplemental_information)}{sc}"
    """content += 'URL de distribution ' + s + fst(
                resource.distribution_url) + sc"""
    """content += 'description de la distribution' + s + fst(
                resource.distribution_description) + sc"""
    content += f"data quality statement{s}{fst(resource.data_quality_statement)}{sc}"

    ext = resource.bbox_polygon.extent
    content += f"extent {s}{fst(ext[0])},{fst(ext[2])},{fst(ext[1])},{fst(ext[3])}{sc}"
    content += f"SRID  {s}{fst(resource.srid)}{sc}"
    content += f"Thumbnail url{s}{fst(resource.thumbnail_url)}{sc}"

    content += f"keywords;{get_keywords(resource)}{s}"
    content += f"category{s}{fst(resource.category)}{sc}"

    content += f"regions{s}"
    for reg in resource.regions.all():
        content += f"{fst(reg.name_en)},"
    content = content[:-1]
    content += sc

    if resource.detail_url.find("/datasets/") > -1:
        layer = Dataset.objects.get(resourcebase_ptr_id=resource.id)
        content += f"attribute data{sc}"
        content += "attribute name;label;description\n"
        for attr in layer.attribute_set.all():
            content += fst(attr.attribute) + s
            content += fst(attr.attribute_label) + s
            content += fst(attr.description) + sc

    @staticmethod
    def __append_contact_role__(content, cr_attr_name, title_in_txt):
        cr = resource.__getattribute__(cr_attr_name)
        if cr is not None or (isinstance(list, cr) and len(0)):
            content += f"{title_in_txt}{sc}"
            for user in cr:
                content += f"name{s}{fst(user.last_name)}{sc}"
                content += f"e-mail{s}{fst(user.email)}{sc}"
        return content

    for role in set(Roles).difference([Roles.OWNER]):
        content = __append_contact_role__(content, role.name, role.label)

    logger = logging.getLogger(__name__)
    logger.error(content)

    return HttpResponse(content, content_type="text/csv")


def csw_render_extra_format_html(request, layeruuid, resname):
    resource = ResourceBase.objects.get(uuid=layeruuid)
    extra_res_md = {}
    try:
        sprt = SpatialRepresentationType.objects.get(id=resource.spatial_representation_type_id)
        extra_res_md["sprt_identifier"] = sprt.identifier
    except ObjectDoesNotExist:
        extra_res_md["sprt_identifier"] = "not filled"
    kw = get_keywords(resource)
    if len(kw) == 0:
        extra_res_md["keywords"] = "no keywords"
    else:
        extra_res_md["keywords"] = get_keywords(resource)

    if resource.detail_url.find("/datasets/") > -1:
        layer = Dataset.objects.get(resourcebase_ptr_id=resource.id)
        extra_res_md["atrributes"] = ""
        for attr in layer.attribute_set.all():
            s = f"<tr><td>{attr.attribute}</td><td>{attr.attribute_label}</td><td>{attr.description}</td></tr>"
            extra_res_md["atrributes"] += s

    extra_res_md["roles"] = []
    for role in Roles:
        cr = resource.__getattribute__(role.name)
        if not isinstance(cr, list):
            cr = [cr]
        users = [{"pk": user.id, "last_name": user.last_name, "email": user.email} for user in cr]
        if users:
            extra_res_md["roles"].append({"label": role.label, "users": users})

    return render(request, "geonode_metadata_full.html", context={"resource": resource, "extra_res_md": extra_res_md})


def resolve_uuid(request, uuid):
    resource = resolve_object(request, ResourceBase, {"uuid": uuid})
    return redirect(resource)
