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

import logging

from .fields import MultiThesauriField

from dal import autocomplete
from taggit.forms import TagField

import six

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import validators
from django.db.models import Prefetch, Q
from django.forms import models
from django.forms import ModelForm
from django.forms.fields import ChoiceField
from django.forms.utils import flatatt
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from django.utils.encoding import (
    force_text,
)

from bootstrap3_datetime.widgets import DateTimePicker
from modeltranslation.forms import TranslationModelForm
from geonode.base.models import HierarchicalKeyword, TopicCategory, Region, License, CuratedThumbnail
from geonode.base.models import ThesaurusKeyword, ThesaurusKeywordLabel
from geonode.documents.models import Document
from geonode.base.enumerations import ALL_LANGUAGES
from geonode.base.widgets import TaggitSelect2Custom

# embrapa #
#from mptt.forms import TreeNodeMultipleChoiceField
#import autocomplete_light
#from autocomplete_light.contrib.taggit_field import TaggitField, TaggitWidget
from geonode.base.models import Embrapa_Keywords, Embrapa_Authors
from django_filters import FilterSet
import requests
from django.utils.text import slugify
from geonode.base.utils import choice_unity, choice_purpose, choice_data_quality_statement, choice_authors, authors_objects_api

logger = logging.getLogger(__name__)

def get_tree_data():
    def rectree(parent, path):
        children_list_of_tuples = list()
        c = Region.objects.filter(parent=parent)
        for child in c:
            children_list_of_tuples.append(
                tuple((path + parent.name, tuple((child.id, child.name))))
            )
            childrens = rectree(child, parent.name + '/')
            if childrens:
                children_list_of_tuples.extend(childrens)

        return children_list_of_tuples

    data = list()
    try:
        t = Region.objects.filter(Q(level=0) | Q(parent=None))
        for toplevel in t:
            data.append(
                tuple((toplevel.id, toplevel.name))
            )
            childrens = rectree(toplevel, '')
            if childrens:
                data.append(
                    tuple((toplevel.name, childrens))
                )
    except Exception:
        pass

    return tuple(data)


class AdvancedModelChoiceIterator(models.ModelChoiceIterator):
    def choice(self, obj):
        return (
            self.field.prepare_value(obj),
            self.field.label_from_instance(obj),
            obj)


class CategoryChoiceField(forms.ModelChoiceField):
    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices

        return AdvancedModelChoiceIterator(self)

    choices = property(_get_choices, ChoiceField._set_choices)

    def label_from_instance(self, obj):
        return '<i class="fa ' + obj.fa_class + ' fa-2x unchecked"></i>' \
               '<i class="fa ' + obj.fa_class + ' fa-2x checked"></i>' \
               '<span class="has-popover" data-container="body" data-toggle="popover" data-placement="top" ' \
               'data-content="' + obj.description + '" trigger="hover">' \
               '<br/><strong>' + obj.gn_description + '</strong></span>'


# NOTE: This is commented as it needs updating to work with select2 and autocomlete light.
#
# class TreeWidget(autocomplete.TaggitSelect2):
#     input_type = 'text'

#     def render(self, name, value, attrs=None):
#         if isinstance(value, basestring):
#             vals = value
#         elif value:
#             vals = ','.join([i.tag.name for i in value])
#         else:
#             vals = ""
#         output = ["""<div class="keywords-container"><span class="input-group">
#                 <input class="form-control"
#                        id="id_resource-keywords"
#                        name="resource-keywords"
#                        value="%s"><br/>""" % (vals)]
#         output.append(
#             '<div id="treeview" class="" style="display: none"></div>')
#         output.append(
#             '<span class="input-group-addon" id="treeview-toggle"><i class="fa fa-folder"></i></span>')
#         output.append('</span></div>')

#         return mark_safe(u'\n'.join(output))


class RegionsMultipleChoiceField(forms.MultipleChoiceField):

    def validate(self, value):
        """
        Validates that the input is a list or tuple.
        """
        if self.required and not value:
            raise forms.ValidationError(
                self.error_messages['required'], code='required')

class RegionsSelect(forms.Select):
    allow_multiple_selected = True

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = []
        final_attrs = self.build_attrs(attrs)
        final_attrs["name"] = name
        output = [
            format_html(
                '<select multiple="multiple"{}>',
                flatatt(final_attrs))]
        options = self.render_options(value)
        if options:
            output.append(options)
        output.append('</select>')
        return mark_safe('\n'.join(output))

    def value_from_datadict(self, data, files, name):
        try:
            getter = data.getlist
        except AttributeError:
            getter = data.get
        return getter(name)

    def render_option_value(
            self,
            selected_choices,
            option_value,
            option_label,
            data_section=None):
        if option_value is None:
            option_value = ''
        option_value = force_text(option_value)
        if option_value in selected_choices:
            selected_html = mark_safe(' selected')
            if not self.allow_multiple_selected:
                # Only allow for a single selection.
                selected_choices.remove(option_value)
        else:
            selected_html = ''

        label = force_text(option_label)

        if data_section is None:
            data_section = ''
        else:
            data_section = force_text(data_section)
            if '/' in data_section:
                label = format_html(
                    '{} [{}]', label, data_section.rsplit(
                        '/', 1)[1])

        return format_html(
            '<option data-section="{}" value="{}"{}>{}</option>',
            data_section,
            option_value,
            selected_html,
            label)

    def render_options(self, selected_choices):

        # Normalize to strings.
        def _region_id_from_choice(choice):
            if isinstance(choice, int) or \
                    (isinstance(choice, six.string_types) and choice.isdigit()):
                return int(choice)
            else:
                return choice.id

        selected_choices = set(force_text(_region_id_from_choice(v)) for v in selected_choices)
        output = []

        output.append(format_html('<optgroup label="{}">', 'Global'))
        for option_value, option_label in self.choices:
            if not isinstance(
                    option_label, (list, tuple)) and isinstance(
                    option_label, six.string_types):
                output.append(
                    self.render_option_value(
                        selected_choices,
                        option_value,
                        option_label))
        output.append('</optgroup>')

        for option_value, option_label in self.choices:
            if isinstance(
                    option_label, (list, tuple)) and not isinstance(
                    option_label, six.string_types):
                output.append(
                    format_html(
                        '<optgroup label="{}">',
                        force_text(option_value)))
                for option in option_label:
                    if isinstance(
                            option, (list, tuple)) and not isinstance(
                            option, six.string_types):
                        if isinstance(
                                option[1][0], (list, tuple)) and not isinstance(
                                option[1][0], six.string_types):
                            for option_child in option[1][0]:
                                output.append(
                                    self.render_option_value(
                                        selected_choices,
                                        *option_child,
                                        data_section=force_text(
                                            option[1][0][0])))
                        else:
                            output.append(
                                self.render_option_value(
                                    selected_choices,
                                    *option[1],
                                    data_section=force_text(
                                        option[0])))
                    else:
                        output.append(
                            self.render_option_value(
                                selected_choices,
                                *option,
                                data_section=force_text(option_value)))
                output.append('</optgroup>')

        return '\n'.join(output)


class CategoryForm(forms.Form):
    category_choice_field = CategoryChoiceField(
        required=False,
        label='*' + _('Category'),
        empty_label=None,
        queryset=TopicCategory.objects.filter(
            is_choice=True) .extra(
            order_by=['description']))

    def clean(self):
        cleaned_data = self.data
        ccf_data = cleaned_data.get("category_choice_field")
        category_mandatory = getattr(settings, 'TOPICCATEGORY_MANDATORY', False)
        if category_mandatory and not ccf_data:
            msg = _("Category is required.")
            self._errors = self.error_class([msg])

        # Always return the full collection of cleaned data.
        return cleaned_data


class TKeywordForm(forms.ModelForm):
    prefix = 'tkeywords'

    class Meta:
        model = Document
        fields = ['tkeywords']

    tkeywords = MultiThesauriField(
        queryset=ThesaurusKeyword.objects.prefetch_related(
            Prefetch('keyword', queryset=ThesaurusKeywordLabel.objects.filter(lang='en'))
        ),
        widget=autocomplete.ModelSelect2Multiple(
            url='thesaurus_autocomplete',
        ),
        label=_("Keywords from Thesaurus"),
        required=False,
        help_text=_("List of keywords from Thesaurus",),
    )


class ResourceBaseDateTimePicker(DateTimePicker):

    def build_attrs(self, base_attrs=None, extra_attrs=None, **kwargs):
        "Helper function for building an attribute dictionary."
        if extra_attrs:
            base_attrs.update(extra_attrs)
        base_attrs.update(kwargs)
        return super(ResourceBaseDateTimePicker, self).build_attrs(base_attrs)
        # return base_attrs

class ResourceBaseForm(TranslationModelForm):
    """Base form for metadata, should be inherited by childres classes of ResourceBase"""

    owner = forms.ModelChoiceField(
        empty_label="Proprietário",
        label=_("Proprietário"),
        required=False,
        queryset=get_user_model().objects.exclude(username='AnonymousUser'),
        widget=autocomplete.ModelSelect2(url='autocomplete_profile'))

    date = forms.DateTimeField(
        label=_("Data de Publicação"),
        localize=True,
        input_formats=['%Y-%m-%d %H:%M %p'],
        widget=ResourceBaseDateTimePicker(options={"format": "YYYY-MM-DD HH:mm a"})
    )
    temporal_extent_start = forms.DateTimeField(
        label=_("Ext. Temporal - Inicio"),
        required=False,
        localize=True,
        input_formats=['%Y-%m-%d %H:%M %p'],
        widget=ResourceBaseDateTimePicker(options={"format": "YYYY-MM-DD HH:mm a"})
    )
    temporal_extent_end = forms.DateTimeField(
        label=_("Ext. Temporal - Fim"),
        required=False,
        localize=True,
        input_formats=['%Y-%m-%d %H:%M %p'],
        widget=ResourceBaseDateTimePicker(options={"format": "YYYY-MM-DD HH:mm a"})
    )

    # embrapa #
    poc = forms.ModelChoiceField(
        empty_label=_("Person outside GeoNode (fill form)"),
        label=_("Ponto de Contato"),
        required=False,
        queryset=get_user_model().objects.exclude(
            username='AnonymousUser'),
        widget=autocomplete.ModelSelect2(url='autocomplete_profile'))

    #poc = forms.ModelMultipleChoiceField(
        #empty_label=_("Person outside GeoNode (fill form)"),
        #label=_("Pontos de Contato"),
        #required=False,
        #help_text='Indicar o(s) autor(es) do conjunto de dados geograficos.',
        #queryset=get_user_model().objects.exclude(
            #username='AnonymousUser'),
        #widget=TaggitSelect2Custom(url='autocomplete_profile'))
        #widget=autocomplete.ModelSelect2(url='autocomplete_profile')

    metadata_author = forms.ModelChoiceField(
        empty_label=_("Person outside GeoNode (fill form)"),
        label=_("Autor do Metadado"),
        required=False,
        queryset=get_user_model().objects.exclude(
            username='AnonymousUser'),
        widget=autocomplete.ModelSelect2(url='autocomplete_profile'))

    keywords = TagField(
        label=_("Termos livres"),
        required=False,
        help_text=_("Caso deseje adicionar alguma palavra-chave que nao consta na lista controlada disponivel no campo 'Palavras-Chave Embrapa', insira palavras-chave adicionais, separando-as por virgula"),
        # widget=TreeWidget(url='autocomplete_hierachical_keyword'), #Needs updating to work with select2
        widget=TaggitSelect2Custom(url='autocomplete_hierachical_keyword'))
    
    # embrapa #
    data_criacao = forms.DateTimeField(
        label = _("Ano de criação do conjunto de dados"),
        localize=True,
        input_formats=['%Y-%m-%d %H:%M %p'],
        help_text="Insira a data de criação do conjunto de dados",
        widget=ResourceBaseDateTimePicker(options={"format": "YYYY-MM-DD HH:mm a"}))

    #embrapa_keywords = forms.ModelMultipleChoiceField(
     #   label="Palavras-Chave Embrapa",
     #   required=False,
     #   help_text="Insira as palavras-chave, para indexacao do documento, de acordo com o vocabulario controlado elaborado pela equipe de geoinformacao da IDE-Embrapa",
     #   queryset=Embrapa_Keywords.objects.all(),
     #   widget=TaggitSelect2Custom(url='autocomplete_embrapa_keywords'))
        
    #outra tentativa
    #embrapa_keywords = EmbrapaKeywordsMultipleChoiceField(
    #    label=_("Palavras-Chave Embrapa"),
    #    required=False,
    #    help_text="Insira as palavras-chave, para indexacao do documento, de acordo com o vocabulario controlado elaborado pela equipe de geoinformacao da IDE-Embrapa",
    #    choices=Embrapa_Keywords.objects.all(),
    #    widget=TaggitSelect2Custom(url='autocomplete_embrapa_keywords')
    #)
    embrapa_keywords = TagField(
        label=_("Palavras-Chave Embrapa"),
        required=False,
        help_text="Insira as palavras-chave, para indexacao do documento, de acordo com o vocabulario controlado elaborado pela equipe de geoinformacao da IDE-Embrapa",
        widget=TaggitSelect2Custom(url='autocomplete_embrapa_keywords')
    )
    
    regions = RegionsMultipleChoiceField(
        label=_("Regiões"),
        required=False,
        choices=get_tree_data(),
        widget=RegionsSelect)

    choice_projeto_acao_gerencial = forms.ChoiceField(
        label=_("Escolha uma das opções:"),
        required=False,
        choices=(('Projeto','Listar Projeto'),('Ação Gerencial','Listar Ação Gerencial')), 
        widget=forms.RadioSelect())
    embrapa_unity = autocomplete.Select2ListChoiceField(
        label=_("Unidade Embrapa"),
        required=False,
        choice_list=choice_unity(),
        widget= autocomplete.ListSelect2(url='autocomplete_embrapa_unity')
    )

    purpose = autocomplete.Select2ListChoiceField(
        label=_("Finalidade"),
        required=False,
        choice_list=choice_purpose(),
        widget= autocomplete.ListSelect2(url='autocomplete_embrapa_purpose')
    )

    embrapa_data_quality_statement = forms.MultipleChoiceField(
        label=_("Declaração da Qualidade do Dado - Fontes"),
        required=False,
        choices=choice_data_quality_statement(),
        widget = autocomplete.Select2Multiple(url='autocomplete_embrapa_data_quality_statement')
    )

    embrapa_autores = forms.MultipleChoiceField(
        label=_("Autores"),
        required=False,
        choices=choice_authors(),
        widget= autocomplete.Select2Multiple(url='autocomplete_embrapa_autores')
    )
    
    regions.widget.attrs = {"size": 20}

    def __init__(self, *args, **kwargs):
        super(ResourceBaseForm, self).__init__(*args, **kwargs)
        print("purpose no forms do base")
        self.fields['purpose'] = autocomplete.Select2ListChoiceField(
            label=_("Finalidade"),
            required=False,
            choice_list=choice_purpose(),
            widget= autocomplete.ListSelect2(url='autocomplete_embrapa_purpose')
        )
        print("data_quality_statement no forms do base")
        self.fields['embrapa_data_quality_statement'] = forms.MultipleChoiceField(
            label=_("Declaração da Qualidade do Dado - Fontes"),
            required=False,
            choices=choice_data_quality_statement(),
            widget= autocomplete.Select2Multiple(url='autocomplete_embrapa_data_quality_statement')
        )
        print("authors no forms do base")
        self.fields['embrapa_autores'] = forms.MultipleChoiceField(
            label=_("Autores"),
            required=False,
            choices=choice_authors(),
            widget= autocomplete.Select2Multiple(url='autocomplete_embrapa_autores')
        )
        for field in self.fields:
            help_text = self.fields[field].help_text
            #self.fields[field].help_text = "Teste"
            if help_text != '':
                self.fields[field].widget.attrs.update(
                    {
                        'placeholder': '',
                        'class': 'has-popover',
                        'data-content': help_text,
                        'data-placement': 'right',
                        'data-container': 'body',
                        'data-html': 'true',
                        })

    def clean_embrapa_autores(self):
        embrapa_autores = self.cleaned_data['embrapa_autores']
        print("Clean autores:")
        print(embrapa_autores)

        name_slug = [i for i in range(len(embrapa_autores))]

        for i in range(len(embrapa_autores)):
            name_slug[i] = slugify(embrapa_autores[i])

        objects_author = authors_objects_api()
        
        if (len(objects_author) > 0):
            for obj in objects_author:
                for i in range(len(embrapa_autores)):
                    if obj.nome == embrapa_autores[i]:
                        embrapa_autores_creates, created = Embrapa_Authors.objects.get_or_create(name=obj.nome, 
                            slug=name_slug[i], depth=1, numchild=0, afiliacao=obj.afiliacao, autoria=obj.autoria)
                        if created:
                            embrapa_autores_creates.save()

        return embrapa_autores

    def clean_embrapa_data_quality_statement(self):
        embrapa_data_quality_statement = self.cleaned_data['embrapa_data_quality_statement']

        return embrapa_data_quality_statement

    #É AQUI QUE TÁ SEPARANDO POR VIRGULAS AS PALAVRAS CHAVE
    def clean_embrapa_keywords(self):
        from urllib.parse import unquote
        from html.entities import codepoint2name

        def unicode_escape(unistr):
            """
            Tidys up unicode entities into HTML friendly entities
            Takes a unicode string as an argument
            Returns a unicode string
            """
            escaped = ""
            for char in unistr:
                if ord(char) in codepoint2name:
                    name = codepoint2name.get(ord(char))
                    escaped += '&%s;' % name if 'nbsp' not in name else ' '
                else:
                    escaped += char
            return escaped
            
        embrapa_keywords = self.cleaned_data['embrapa_keywords']
        embrapa_keywords_tmp = []
        chars = ['À','Á','Â','Ã','Å','Ç','È','É','Ê','Ì','Í','Î','Ò','Ó','Ô','Õ','Ö','Ù','Ú','Û','Ý','à','á','â','ã','ç','è','é','ê','ì','í','î','ò','ó','ô','õ','ù','ú','û', ' ']
        utf = ['%C0','%C1','%C2','%C3','%C5','%C7','%C8','%C9','%CA','%CC','%CD','%CE','%D2','%D3','%D4','%D5','%D6','%D9','%DA','%DB','%DD','%E0','%E1','%E2','%E3','%E7','%E8','%E9','%EA','%EC','%ED','%EE','%F2','%F3','%F4','%F5','%F9','%FA','%FB', '%20']
        i = 0
        for key in embrapa_keywords:
            i = 0
            for ut in utf:
                if key.find(ut) > -1:
                    key = key.replace(ut, chars[i])
                i += 1
            embrapa_keywords_tmp.append(key)

        embrapa_keywords = embrapa_keywords_tmp

        _unsescaped_embrapa_kwds = []
        for k in embrapa_keywords:
            _k = unquote(('%s' % k)).split(",")
            if not isinstance(_k, six.string_types):
                for _kk in [x.strip() for x in _k]:
                    # Simulate JS Unescape
                    _kk = _kk.replace('%u', r'\u').\
                        encode('unicode-escape').replace(b'\\\\u',
                                                         b'\\u').decode('unicode-escape') if '%u' in _kk else _kk
                    _ek = Embrapa_Keywords.objects.filter(name__iexact='%s' % _kk.strip())
                    
                    if _ek and len(_ek) > 0:
                        _unsescaped_embrapa_kwds.append(str(_ek[0]))
                    else:
                        _unsescaped_embrapa_kwds.append(str(_kk))
            else:
                _ek = Embrapa_Keywords.objects.filter(name__iexact=_k.strip())
                if _ek and len(_ek) > 0:
                    _unsescaped_embrapa_kwds.append(str(_ek[0]))
                else:
                    _unsescaped_embrapa_kwds.append(str(_k))
        return _unsescaped_embrapa_kwds


    #É AQUI QUE TÁ SEPARANDO POR VIRGULAS AS PALAVRAS CHAVE
    def clean_keywords(self):
        from urllib.parse import unquote
        from html.entities import codepoint2name

        def unicode_escape(unistr):
            """
            Tidys up unicode entities into HTML friendly entities
            Takes a unicode string as an argument
            Returns a unicode string
            """
            escaped = ""
            for char in unistr:
                if ord(char) in codepoint2name:
                    name = codepoint2name.get(ord(char))
                    escaped += '&%s;' % name if 'nbsp' not in name else ' '
                else:
                    escaped += char
            return escaped

        keywords = self.cleaned_data['keywords']

        keywords_tmp = []
        chars = ['À','Á','Â','Ã','Å','Ç','È','É','Ê','Ì','Í','Î','Ò','Ó','Ô','Õ','Ö','Ù','Ú','Û','Ý','à','á','â','ã','ç','è','é','ê','ì','í','î','ò','ó','ô','õ','ù','ú','û', ' ']
        utf = ['%C0','%C1','%C2','%C3','%C5','%C7','%C8','%C9','%CA','%CC','%CD','%CE','%D2','%D3','%D4','%D5','%D6','%D9','%DA','%DB','%DD','%E0','%E1','%E2','%E3','%E7','%E8','%E9','%EA','%EC','%ED','%EE','%F2','%F3','%F4','%F5','%F9','%FA','%FB', '%20']
        i = 0
        for key in keywords:
            i = 0
            for ut in utf:
                if key.find(ut) > -1:
                    key = key.replace(ut, chars[i])
                i += 1
            keywords_tmp.append(key)

        keywords = keywords_tmp

        _unsescaped_kwds = []
        for k in keywords:
            _k = unquote(('%s' % k)).split(",")
            if not isinstance(_k, six.string_types):
                for _kk in [x.strip() for x in _k]:
                    # Simulate JS Unescape
                    _kk = _kk.replace('%u', r'\u').\
                        encode('unicode-escape').replace(b'\\\\u',
                                                         b'\\u').decode('unicode-escape') if '%u' in _kk else _kk
                    _hk = HierarchicalKeyword.objects.filter(name__iexact='%s' % _kk.strip())
                    if _hk and len(_hk) > 0:
                        _unsescaped_kwds.append(str(_hk[0]))
                    else:
                        _unsescaped_kwds.append(str(_kk))
            else:
                _hk = HierarchicalKeyword.objects.filter(name__iexact=_k.strip())
                if _hk and len(_hk) > 0:
                    _unsescaped_kwds.append(str(_hk[0]))
                else:
                    _unsescaped_kwds.append(str(_k))
        return _unsescaped_kwds

    class Meta:
        exclude = (
            'contacts',
            'name',
            'uuid',
            'bbox_x0',
            'bbox_x1',
            'bbox_y0',
            'bbox_y1',
            'srid',
            'category',
            'csw_typename',
            'csw_schema',
            'csw_mdsource',
            'csw_type',
            'csw_wkt_geometry',
            'metadata_uploaded',
            'metadata_xml',
            'csw_anytext',
            'popular_count',
            'share_count',
            'thumbnail',
            'charset',
            'rating',
            'detail_url',
            'tkeywords',
        )

# testar esse aqui também
class ValuesListField(forms.Field):

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return []

        value = [item.strip() for item in value.split(',') if item.strip()]

        return value

    def clean(self, value):
        value = self.to_python(value)
        self.validate(value)
        self.run_validators(value)
        return value


class BatchEditForm(forms.Form):
    LANGUAGES = (('', '--------'),) + ALL_LANGUAGES
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False)
    owner = forms.ModelChoiceField(
        queryset=get_user_model().objects.all(),
        required=False)
    category = forms.ModelChoiceField(
        queryset=TopicCategory.objects.all(),
        required=False)
    license = forms.ModelChoiceField(
        queryset=License.objects.all(),
        required=False)
    regions = forms.ModelChoiceField(
        queryset=Region.objects.all(),
        required=False)
    date = forms.DateTimeField(required=False)
    language = forms.ChoiceField(
        required=False,
        choices=LANGUAGES,
    )
    keywords = forms.CharField(required=False)


class BatchPermissionsForm(forms.Form):
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False)
    user = forms.ModelChoiceField(
        queryset=get_user_model().objects.all(),
        required=False)
    permission_type = forms.MultipleChoiceField(
        required=True,
        widget=forms.CheckboxSelectMultiple,
        choices=(
            ('r', 'Read'),
            ('w', 'Write'),
            ('d', 'Download'),
        ),
    )
    mode = forms.ChoiceField(
        required=True,
        widget=forms.RadioSelect,
        choices=(
            ('set', 'Set'),
            ('unset', 'Unset'),
        ),
    )


class CuratedThumbnailForm(ModelForm):

    class Meta:
        model = CuratedThumbnail
        fields = ['img']
