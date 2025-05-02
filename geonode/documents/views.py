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
import json
import shutil
import logging
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.template import loader
from django.views.generic.edit import CreateView, UpdateView
from django.http import HttpResponse, HttpResponseRedirect

from geonode.assets.handlers import asset_handler_registry
from geonode.assets.utils import get_default_asset
from geonode.base.api.exceptions import geonode_exception_handler
from geonode.client.hooks import hookset
from geonode.utils import mkdtemp
from geonode.base import register_event
from geonode.base.bbox_utils import BBOXHelper
from geonode.storage.manager import storage_manager
from geonode.resource.manager import resource_manager
from geonode.base import enumerations

from pathlib import Path

from .utils import get_download_response

from .models import Document
from .forms import DocumentCreateForm, DocumentReplaceForm

logger = logging.getLogger("geonode.documents.views")

ALLOWED_DOC_TYPES = settings.ALLOWED_DOCUMENT_TYPES


def document_download(request, docid):
    response = get_download_response(request, docid, attachment=True)
    return response


def document_link(request, docid):
    response = get_download_response(request, docid)
    return response


def document_embed(request, docid):
    document = get_object_or_404(Document, pk=docid)

    if not request.user.has_perm("base.download_resourcebase", obj=document.get_self_resource()):
        return HttpResponse(
            loader.render_to_string(
                "401.html", context={"error_message": _("You are not allowed to view this document.")}, request=request
            ),
            status=401,
        )
    if document.is_image:
        if document.doc_url:
            imageurl = document.doc_url
        else:
            imageurl = reverse("document_link", args=(document.id,))
        context_dict = {
            "image_url": imageurl,
            "resource": document.get_self_resource(),
        }
        return render(request, "documents/document_embed.html", context_dict)
    else:
        context_dict = {
            "document_link": reverse("document_link", args=(document.id,)),
            "resource": document.get_self_resource(),
        }
        return render(request, "documents/document_embed.html", context_dict)


class DocumentUploadView(CreateView):
    http_method_names = ["post"]
    form_class = DocumentCreateForm

    def post(self, request, *args, **kwargs):
        self.object = None
        try:
            return super().post(request, *args, **kwargs)
        except Exception as e:
            exception_response = geonode_exception_handler(e, {})
            return HttpResponse(
                json.dumps(exception_response.data),
                content_type="application/json",
                status=exception_response.status_code,
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ALLOWED_DOC_TYPES"] = ALLOWED_DOC_TYPES
        return context

    def form_invalid(self, form):
        messages.error(self.request, f"{form.errors}")
        if self.request.GET.get("no__redirect", False):
            plaintext_errors = []
            for field in form.errors.values():
                plaintext_errors.append(field.data[0].message)
            out = {"success": False}
            out["message"] = ".".join(plaintext_errors)
            status_code = 400
            return HttpResponse(json.dumps(out), content_type="application/json", status=status_code)
        else:
            form.name = None
            form.title = None
            form.doc_file = None
            form.doc_url = None
            return self.render_to_response(self.get_context_data(request=self.request, form=form))

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        doc_form = form.cleaned_data

        file = doc_form.pop("doc_file", None)
        if file:
            tempdir = mkdtemp()
            dirname = os.path.basename(tempdir)
            name = Path(file.name)
            filepath = storage_manager.save(f"{dirname}/{name.stem}{name.suffix.lower()}", file)
            storage_path = storage_manager.path(filepath)
            self.object = resource_manager.create(
                None,
                resource_type=Document,
                defaults=dict(
                    owner=self.request.user,
                    doc_url=doc_form.pop("doc_url", None),
                    title=doc_form.pop("title", file.name),
                    description=doc_form.pop("abstract", None),
                    extension=doc_form.pop("extension", None),
                    link_type="uploaded",  # should be in geonode.base.enumerations.LINK_TYPES
                    data_title=doc_form.pop("title", file.name),
                    data_type=doc_form.pop("extension", None),
                    files=[storage_path],
                ),
            )

            # Removing the temp file
            # TODO: creating a file and then cloning it as an Asset may be slow: we may want to
            #       create the file directly in the asset dir or to move it
            logger.info(f"Removing document temp dir {tempdir}")
            shutil.rmtree(tempdir, ignore_errors=True)

        else:
            self.object = resource_manager.create(
                None,
                resource_type=Document,
                defaults=dict(
                    owner=self.request.user,
                    doc_url=doc_form.pop("doc_url", None),
                    title=doc_form.pop("title", None),
                    extension=doc_form.pop("extension", None),
                    sourcetype=enumerations.SOURCE_TYPE_REMOTE,
                ),
            )

        self.object.handle_moderated_uploads()
        self.object.set_default_permissions(owner=self.request.user, created=True)

        abstract = None
        date = None
        regions = []
        keywords = []
        bbox = None
        url = hookset.document_detail_url(self.object)

        out = {"success": False}

        if getattr(settings, "EXIF_ENABLED", False):
            try:
                from geonode.documents.exif.utils import exif_extract_metadata_doc

                exif_metadata = exif_extract_metadata_doc(self.object)
                if exif_metadata:
                    date = exif_metadata.get("date", None)
                    keywords.extend(exif_metadata.get("keywords", []))
                    bbox = exif_metadata.get("bbox", None)
                    abstract = exif_metadata.get("abstract", None)
            except Exception:
                logger.debug("Exif extraction failed.")

        resource_manager.update(
            self.object.uuid,
            instance=self.object,
            keywords=keywords,
            regions=regions,
            vals=dict(
                abstract=abstract,
                date=date,
                date_type="Creation",
                bbox_polygon=BBOXHelper.from_xy(bbox).as_polygon() if bbox else None,
            ),
            notify=True,
        )
        resource_manager.set_thumbnail(self.object.uuid, instance=self.object, overwrite=False)

        register_event(self.request, enumerations.EventType.EVENT_UPLOAD, self.object)

        if self.request.GET.get("no__redirect", False):
            out["success"] = True
            out["url"] = url
            if out["success"]:
                status_code = 200
            else:
                status_code = 400
            return HttpResponse(json.dumps(out), content_type="application/json", status=status_code)
        else:
            return HttpResponseRedirect(url)


class DocumentUpdateView(UpdateView):
    template_name = "documents/document_replace.html"
    pk_url_kwarg = "docid"
    form_class = DocumentReplaceForm
    queryset = Document.objects.all()
    context_object_name = "document"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            return super().post(request, *args, **kwargs)
        except Exception as e:
            exception_response = geonode_exception_handler(e, {})
            return HttpResponse(
                json.dumps(exception_response.data),
                content_type="application/json",
                status=exception_response.status_code,
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ALLOWED_DOC_TYPES"] = ALLOWED_DOC_TYPES
        return context

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        doc_form = form.cleaned_data

        file = doc_form.pop("doc_file", None)
        if file:
            tempdir = mkdtemp()
            dirname = os.path.basename(tempdir)
            filepath = storage_manager.save(os.path.join(dirname, file.name), file)
            storage_path = storage_manager.path(filepath)
            self.object = resource_manager.update(
                self.object.uuid, instance=self.object, vals=dict(owner=self.request.user)
            )

            # replace data in existing asset
            asset = get_default_asset(self.object, link_type="uploaded")
            if asset:
                asset_handler_registry.get_handler(asset).replace_data(asset, [storage_path])

            if tempdir != os.path.dirname(storage_path):
                shutil.rmtree(tempdir, ignore_errors=True)

        register_event(self.request, enumerations.EventType.EVENT_CHANGE, self.object)
        url = hookset.document_detail_url(self.object)
        return HttpResponseRedirect(url)
