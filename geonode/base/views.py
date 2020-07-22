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
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.conf import settings

from guardian.shortcuts import get_objects_for_user
from dal import views, autocomplete

from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.base.models import ResourceBase, Region, HierarchicalKeyword, ThesaurusKeywordLabel, Embrapa_Keywords
from geonode.utils import resolve_object
from geonode.security.utils import get_visible_resources
from .forms import BatchEditForm
from .forms import CuratedThumbnailForm

# embrapa #
from django.db.models import Q
from datetime import datetime
from geonode.base.utils import get_last_update, choice_data_quality_statement, choice_authors, choice_unity, choice_purpose

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

    if "cancel" in request.POST:
        return HttpResponseRedirect(
            '/admin/{model}s/{model}/'.format(model=model.lower())
        )

    if request.method == 'POST':
        form = BatchEditForm(request.POST)
        if form.is_valid():
            for resource in Resource.objects.filter(id__in=ids.split(',')):
                resource.group = form.cleaned_data['group'] or resource.group
                resource.owner = form.cleaned_data['owner'] or resource.owner
                resource.category = form.cleaned_data['category'] or resource.category
                resource.license = form.cleaned_data['license'] or resource.license
                resource.date = form.cleaned_data['date'] or resource.date
                #embrapa#
                #resource.data_criacao = form.cleaned_data['data_criacao'] or resource.data_criacao
                resource.language = form.cleaned_data['language'] or resource.language
                new_region = form.cleaned_data['regions']
                if new_region:
                    resource.regions.add(new_region)
                keywords = form.cleaned_data['keywords']
                if keywords:
                    resource.keywords.clear()
                    for word in keywords.split(','):
                        resource.keywords.add(word.strip())
                #embrapa#
                #embrapa_keywords = form.cleaned_data['embrapa_keywords']
                #if embrapa_keywords:
                #    resource.embrapa_keywords.clear()
                #    for embrapa_word in embrapa_keywords.split(','):
                #        resource.embrapa_keywords.add(embrapa_word.strip())

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


def thumbnail_upload(
        request,
        res_id,
        template='base/thumbnail_upload.html'):

    try:
        res = resolve_object(
            request, ResourceBase, {
                'id': res_id}, 'base.change_resourcebase')

    except PermissionDenied:
        return HttpResponse(
            'You are not allowed to change permissions for this resource',
            status=401,
            content_type='text/plain')

    form = CuratedThumbnailForm()

    if request.method == 'POST':
        if 'remove-thumb' in request.POST:
            if hasattr(res, 'curatedthumbnail'):
                res.curatedthumbnail.delete()
        else:
            form = CuratedThumbnailForm(request.POST, request.FILES)
            if form.is_valid():
                ct = form.save(commit=False)
                # remove existing thumbnail if any
                if hasattr(res, 'curatedthumbnail'):
                    res.curatedthumbnail.delete()
                ct.resource = res
                ct.save()
        return HttpResponseRedirect(request.path_info)

    return render(request, template, context={
        'resource': res,
        'form': form
    })


class SimpleSelect2View(autocomplete.Select2QuerySetView):
    """ Generic select2 view for autocompletes
        Params:
            model: model to perform the autocomplete query on
            filter_arg: property to filter with ie. name__icontains
    """

    def __init__(self, *args, **kwargs):
        super(views.BaseQuerySetView, self).__init__(*args, **kwargs)
        if not hasattr(self, 'filter_arg'):
            raise AttributeError("SimpleSelect2View missing required 'filter_arg' argument")

    def get_queryset(self):
        qs = super(views.BaseQuerySetView, self).get_queryset()
        if self.q:
            qs = qs.filter(**{self.filter_arg: self.q})
        return qs


class ResourceBaseAutocomplete(autocomplete.Select2QuerySetView):
    """ Base resource autocomplete - searches all the resources by title
        returns any visible resources in this queryset for autocomplete
    """

    def get_queryset(self):
        request = self.request

        permitted = get_objects_for_user(request.user, 'base.view_resourcebase')
        qs = ResourceBase.objects.all().filter(id__in=permitted)

        if self.q:
            qs = qs.filter(title__icontains=self.q).order_by('title')

        return get_visible_resources(
            qs,
            request.user if request else None,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)[:100]


class RegionAutocomplete(SimpleSelect2View):

    model = Region
    filter_arg = 'name__icontains'


class HierarchicalKeywordAutocomplete(SimpleSelect2View):

    model = HierarchicalKeyword
    filter_arg = 'slug__icontains'

### embrapa ###
'''
class EmbrapaKeywordsAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        search_fields = ['^name']

        qs = Embrapa_Keywords.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs
'''
#class Embrapa_PurposeAutocomplete(autocomplete.Select2QuerySetView):
#    def get_queryset(self):
#        search_fields = ['^title']

        #form = BatchEditForm(request.GET)
        # Verificar se isso da certo pra poder fazer o filtro tanto para ação gerencial quanto para projeto para separá-los
        # Tentar alocar a chamada da api e o método de save aqui
        # SE A DATA QUE É DE HOJE (MENOS) A DATA QUE VEIO DO BANCO É (MAIOR) QUE O TEMPO EM SEGUNDOS DE UM MÊS, 
        # DAI ENTRA PRA SALVAR, SE NÃO, CONTINUA (E SE SALVAR DEPOIS DE UM TEMPO, ATUALIZAR A DATA DE SAVE COM UM UPDATE VIA DJANGO)
        # Criar uma tabela pra salvar a data e atualizar ela quando for salvar a base de dados vindos da api
        
#        print("Teste no views.py do base - Purpose")
#        print("Unidade no purpose:")
#        print(settings.EMBRAPA_UNITY_DEFAULT)

#        qs = Embrapa_Purpose.objects.all()

#        if self.q:
#            qs = qs.filter(Q(title__icontains=self.q) | Q(identifier__icontains=self.q) | Q(project_code__icontains=self.q))

#        return qs

class EmbrapaAuthorsAutocomplete(autocomplete.Select2GroupListView):
    def get_list(self):

        if not self.q:
            #print("Tá vazia")
            embrapa_autores = None
        else:
            embrapa_autores = choice_authors()


        #print("Views autores:")

        return embrapa_autores
        #return [item[0][1] for item in embrapa_autores if item[0][1] == item[0][1]]


class EmbrapaDataQualityStatementAutocomplete(autocomplete.Select2GroupListView):
    def get_list(self):

        embrapa_data_quality_statements = choice_data_quality_statement()

        #print("Views declaração da qualidade do dado:")

        return embrapa_data_quality_statements

class EmbrapaPurposeAutocomplete(autocomplete.Select2GroupListView):
    def get_list(self):

        embrapa_purposes = choice_purpose()

        #print("Unidade da Embrapa:")
        #print(settings.EMBRAPA_UNITY_DEFAULT)

        return embrapa_purposes

class EmbrapaUnityAutocomplete(autocomplete.Select2GroupListView):
    def get_list(self):

        embrapa_unities = choice_unity()

        # Derrubar a tabela de embrapa_unities e embrapa_purpose, transforma-los em charfields na camada.
        # E vai ser tupla mesmo, gerada pela lista retornada da api

        #print("self.q:")
        #print(self.q)

        if self.q:
            settings.EMBRAPA_UNITY_DEFAULT = self.q

        return embrapa_unities

class EmbrapaKeywordsAutocomplete(SimpleSelect2View):

    model = Embrapa_Keywords
    filter_arg = 'slug__icontains'


class ThesaurusKeywordLabelAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        thesaurus = settings.THESAURUS
        tname = thesaurus['name']
        lang = 'en'

        # Filters thesaurus results based on thesaurus name and language
        qs = ThesaurusKeywordLabel.objects.all().filter(
            keyword__thesaurus__identifier=tname,
            lang=lang
        )

        if self.q:
            qs = qs.filter(label__icontains=self.q)

        return qs

    # Overides the get results method to return custom json to frontend
    def get_results(self, context):
        return [
            {
                'id': self.get_result_value(result.keyword),
                'text': self.get_result_label(result),
                'selected_text': self.get_selected_result_label(result),
            } for result in context['object_list']
        ]
