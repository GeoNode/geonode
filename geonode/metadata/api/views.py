#########################################################################
#
# Copyright (C) 2024 OSGeo
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
import logging

from dal import autocomplete
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from django.contrib.auth import get_user_model
from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse
from django.utils.translation.trans_real import get_language_from_request
from django.utils.translation import get_language, gettext as _
from django.db.models import Q

from geonode.base.api.permissions import UserHasPerms
from geonode.base.models import ResourceBase, ThesaurusKeyword, ThesaurusKeywordLabel, TopicCategory, License
from geonode.base.utils import remove_country_from_languagecode
from geonode.base.views import LinkedResourcesAutocomplete, RegionAutocomplete, HierarchicalKeywordAutocomplete
from geonode.groups.models import GroupProfile
from geonode.metadata.i18n import get_localized_label
from geonode.metadata.manager import metadata_manager
from geonode.people.utils import get_available_users

logger = logging.getLogger(__name__)


class MetadataViewSet(ViewSet):
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrReadOnly, UserHasPerms]

    """
    Simple viewset that return the metadata JSON schema
    """

    queryset = ResourceBase.objects.all()

    def list(self, request):
        pass

    # Get the JSON schema
    # A pk argument is set for futured multiple schemas
    @action(detail=False, methods=["get"], url_path=r"schema(?:/(?P<pk>\d+))?", url_name="schema")
    def schema(self, request, pk=None):
        """
        The user is able to export her/his keys with
        resource scope.
        """

        lang = request.query_params.get("lang", get_language_from_request(request)[:2])
        schema = metadata_manager.get_schema(lang)

        if schema:
            return Response(schema)

        else:
            response = {"Message": "Schema not found"}
            return Response(response)

    # Handle the JSON schema instance
    @action(
        detail=False,
        methods=["get", "put"],
        url_path=r"instance/(?P<pk>\d+)",
        url_name="schema_instance",
        permission_classes=[
            UserHasPerms(
                perms_dict={
                    "default": {
                        "GET": ["base.view_resourcebase"],
                        "PUT": ["change_resourcebase_metadata"],
                    }
                }
            )
        ],
    )
    def schema_instance(self, request, pk=None):
        try:
            resource = ResourceBase.objects.get(pk=pk)
            lang = request.query_params.get("lang", get_language_from_request(request)[:2])

            if request.method == "GET":
                schema_instance = metadata_manager.build_schema_instance(resource, lang)
                return JsonResponse(
                    schema_instance, content_type="application/schema-instance+json", json_dumps_params={"indent": 3}
                )

            elif request.method == "PUT":
                logger.debug(f"handling request {request.method}")
                # try:
                #     logger.debug(f"handling content {json.dumps(request.data, indent=3)}")
                # except Exception as e:
                #     logger.warning(f"Can't parse JSON {request.data}: {e}")
                errors = metadata_manager.update_schema_instance(resource, request.data, lang)

                msg_t = (
                    ("m_metadata_update_error", "Some errors were found while updating the resource")
                    if errors
                    else ("m_metadata_update_ok", "The resource was updated successfully")
                )
                msg = get_localized_label(lang, msg_t[0]) or msg_t[1]

                response = {
                    "message": msg,
                    "extraErrors": errors,
                }

                return Response(response, status=422 if errors else 200)

        except ResourceBase.DoesNotExist:
            result = {"message": "The dataset was not found"}
            return Response(result, status=404)


def tkeywords_autocomplete(request: WSGIRequest, thesaurusid):

    lang = remove_country_from_languagecode(get_language())
    all_keywords_qs = ThesaurusKeyword.objects.filter(thesaurus_id=thesaurusid)

    # try find results found for given language e.g. (en-us) if no results found remove country code from language to (en) and try again
    localized_k_ids_qs = ThesaurusKeywordLabel.objects.filter(lang=lang, keyword_id__in=all_keywords_qs).values(
        "keyword_id"
    )

    # consider all the keywords that do not have a translation in the requested language
    keywords_not_translated_qs = (
        all_keywords_qs.exclude(id__in=localized_k_ids_qs).order_by("id").distinct("id").values("id")
    )

    qs = ThesaurusKeywordLabel.objects.filter(lang=lang, keyword_id__in=all_keywords_qs).order_by("label")
    # if q := request.query_params.get("q", None):
    if q := request.GET.get("q", None):
        qs = qs.filter(label__istartswith=q)

    ret = []
    for tkl in qs.all():
        ret.append(
            {
                "id": tkl.keyword.about,
                "label": tkl.label,
            }
        )
    for tk in all_keywords_qs.filter(id__in=keywords_not_translated_qs).order_by("alt_label").all():
        ret.append(
            {
                "id": tk.about,
                "label": f"! {tk.alt_label}",
            }
        )

    return JsonResponse({"results": ret})


def categories_autocomplete(request: WSGIRequest):
    qs = TopicCategory.objects.order_by("gn_description")

    if q := request.GET.get("q", None):
        qs = qs.filter(gn_description__istartswith=q)

    ret = []
    for record in qs.all():
        ret.append(
            {
                "id": record.identifier,
                "label": _(record.gn_description),
            }
        )

    return JsonResponse({"results": ret})


def licenses_autocomplete(request: WSGIRequest):
    qs = License.objects.order_by("name")

    if q := request.GET.get("q", None):
        qs = qs.filter(name__istartswith=q)

    ret = []
    for record in qs.all():
        ret.append(
            {
                "id": record.identifier,
                "label": _(record.name),
            }
        )

    return JsonResponse({"results": ret})


class ProfileAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if self.request and self.request.user:
            qs = get_available_users(self.request.user)
        else:
            qs = get_user_model().objects.none()

        if self.q:
            qs = qs.filter(
                Q(username__icontains=self.q)
                | Q(email__icontains=self.q)
                | Q(first_name__icontains=self.q)
                | Q(last_name__icontains=self.q)
            )

        return qs

    def get_results(self, context):
        def get_label(user):
            names = [n for n in (user.first_name, user.last_name) if n]
            postfix = f" ({' '.join(names)})" if names else ""
            return f"{user.username}{postfix}"

        """Return data for the 'results' key of the response."""
        return [{"id": self.get_result_value(result), "label": get_label(result)} for result in context["object_list"]]


class MetadataLinkedResourcesAutocomplete(LinkedResourcesAutocomplete):
    def get_results(self, context):
        return [
            {"id": self.get_result_value(result), "label": self.get_result_label(result)}
            for result in context["object_list"]
        ]


class MetadataRegionsAutocomplete(RegionAutocomplete):
    def get_results(self, context):
        return [
            {"id": self.get_result_value(result), "label": self.get_result_label(result)}
            for result in context["object_list"]
        ]


class MetadataHKeywordAutocomplete(HierarchicalKeywordAutocomplete):
    def get_results(self, context):
        return [self.get_result_label(result) for result in context["object_list"]]


class MetadataGroupAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        user = self.request.user if self.request else None

        if not user:
            qs = GroupProfile.objects.none()
        elif user.is_superuser or user.is_staff:
            qs = GroupProfile.objects.all()
        else:
            qs = GroupProfile.objects.filter(groupmember__user=user)

        qs = qs.order_by("title")
        if self.q:
            qs = qs.filter(title__icontains=self.q)

        return qs

    def get_results(self, context):
        return [{"id": self.get_result_value(result), "label": result.title} for result in context["object_list"]]
