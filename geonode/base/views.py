# -*- coding: utf-8 -*-
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


# Geonode functionality
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.maps.models import Map
from .forms import BatchEditForm


def batch_modify(request, ids, model):
    if not request.user.is_superuser:
        raise PermissionDenied
    if model == 'Document':
        Resource = Document
    if model == 'Layer':
        Resource = Layer
    if model == 'Map':
        Resource = Map
    template = 'base/batch_edit.html'
    if request.method == 'POST':
        form = BatchEditForm(request.POST)
        if form.is_valid():
            for resource in Resource.objects.filter(id__in=ids.split(',')):
                resource.group = form.cleaned_data['group'] or resource.group
                resource.owner = form.cleaned_data['owner'] or resource.owner
                resource.category = form.cleaned_data['category'] or resource.category
                resource.license = form.cleaned_data['license'] or resource.license
                resource.date = form.cleaned_data['date'] or resource.date
                resource.language = form.cleaned_data['language'] or resource.language
                new_region = form.cleaned_data['regions']
                if new_region:
                    resource.regions.add(new_region)
                keywords = form.cleaned_data['keywords']
                if keywords:
                    resource.keywords.clear()
                    for word in keywords.split(','):
                        resource.keywords.add(word.strip())
                resource.save()
            return HttpResponseRedirect(
                '/admin/{model}s/{model}/'.format(model=model.lower())
            )
        return render(
            request,
            template,
            context={
                'form': form,
                'ids': ids,
                'model': model,
            }
        )
    form = BatchEditForm()
    return render(
        request,
        template,
        context={
            'form': form,
            'ids': ids,
            'model': model,
        }
    )
