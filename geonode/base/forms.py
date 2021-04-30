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
import re
import six
import html
import logging

from tinymce.widgets import TinyMCE

from .fields import MultiThesauriField

from dal import autocomplete
from taggit.forms import TagField

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

from geonode.base.models import HierarchicalKeyword, TopicCategory, Region, License, CuratedThumbnail, \
    ResourceBase
from geonode.base.models import ThesaurusKeyword, ThesaurusKeywordLabel
from geonode.documents.models import Document
from geonode.base.enumerations import ALL_LANGUAGES
from geonode.base.widgets import TaggitSelect2Custom
from geonode.layers.models import Layer

logger = logging.getLogger(__name__)


def get_tree_data():
    def rectree(parent, path):
        children_list_of_tuples = list()
        c = Region.objects.filter(parent=parent)
        for child in c:
            children_list_of_tuples.append(
                tuple((path + parent.name, tuple((child.id, child.name))))
            )
            childrens = rectree(child, f"{parent.name}/")
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
        label=f"*{_('Category')}",
        empty_label=None,
        queryset=TopicCategory.objects.filter(
            is_choice=True).extra(
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
        help_text=_("List of keywords from Thesaurus", ),
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
    abstract = forms.CharField(
        label=_("Abstract"),
        required=False,
        widget=TinyMCE())
    purpose = forms.CharField(
        label=_("Purpose"),
        required=False,
        widget=TinyMCE())
    constraints_other = forms.CharField(
        label=_("Other constraints"),
        required=False,
        widget=TinyMCE())
    supplemental_information = forms.CharField(
        label=_('Supplemental information'),
        required=False,
        widget=TinyMCE())
    data_quality_statement = forms.CharField(
        label=_("Data quality statement"),
        required=False,
        widget=TinyMCE())
    owner = forms.ModelChoiceField(
        empty_label=_("Owner"),
        label=_("Owner"),
        required=False,
        queryset=get_user_model().objects.exclude(username='AnonymousUser'),
        widget=autocomplete.ModelSelect2(url='autocomplete_profile'))

    date = forms.DateTimeField(
        label=_("Date"),
        localize=True,
        input_formats=['%Y-%m-%d %H:%M %p'],
        widget=ResourceBaseDateTimePicker(options={"format": "YYYY-MM-DD HH:mm a"})
    )
    temporal_extent_start = forms.DateTimeField(
        label=_("temporal extent start"),
        required=False,
        localize=True,
        input_formats=['%Y-%m-%d %H:%M %p'],
        widget=ResourceBaseDateTimePicker(options={"format": "YYYY-MM-DD HH:mm a"})
    )
    temporal_extent_end = forms.DateTimeField(
        label=_("temporal extent end"),
        required=False,
        localize=True,
        input_formats=['%Y-%m-%d %H:%M %p'],
        widget=ResourceBaseDateTimePicker(options={"format": "YYYY-MM-DD HH:mm a"})
    )

    poc = forms.ModelChoiceField(
        empty_label=_("Person outside GeoNode (fill form)"),
        label=_("Point of Contact"),
        required=False,
        queryset=get_user_model().objects.exclude(
            username='AnonymousUser'),
        widget=autocomplete.ModelSelect2(url='autocomplete_profile'))

    metadata_author = forms.ModelChoiceField(
        empty_label=_("Person outside GeoNode (fill form)"),
        label=_("Metadata Author"),
        required=False,
        queryset=get_user_model().objects.exclude(
            username='AnonymousUser'),
        widget=autocomplete.ModelSelect2(url='autocomplete_profile'))

    keywords = TagField(
        label=_("Free-text Keywords"),
        required=False,
        help_text=_("A space or comma-separated list of keywords. Use the widget to select from Hierarchical tree."),
        # widget=TreeWidget(url='autocomplete_hierachical_keyword'), #Needs updating to work with select2
        widget=TaggitSelect2Custom(url='autocomplete_hierachical_keyword'))

    """
    regions = TreeNodeMultipleChoiceField(
        label=_("Regions"),
        required=False,
        queryset=Region.objects.all(),
        level_indicator=u'___')
    """
    regions = RegionsMultipleChoiceField(
        label=_("Regions"),
        required=False,
        choices=get_tree_data(),
        widget=RegionsSelect)

    regions.widget.attrs = {"size": 20}

    def __init__(self, *args, **kwargs):
        super(ResourceBaseForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            help_text = self.fields[field].help_text
            if help_text != '':
                self.fields[field].widget.attrs.update(
                    {
                        'class': 'has-popover',
                        'data-content': help_text,
                        'data-placement': 'right',
                        'data-container': 'body',
                        'data-html': 'true'})

    def disable_keywords_widget_for_non_superuser(self, user):
        if settings.FREETEXT_KEYWORDS_READONLY and not user.is_superuser:
            self['keywords'].field.disabled = True

    def clean_keywords(self):
        keywords = self.cleaned_data['keywords']
        _unsescaped_kwds = []
        for k in keywords:
            _k = ('%s' % re.sub(r'%([A-Z0-9]{2})', r'&#x\g<1>;', k.strip())).split(",")
            if not isinstance(_k, six.string_types):
                for _kk in [html.unescape(x.strip()) for x in _k]:
                    # Simulate JS Unescape
                    _kk = _kk.replace('%u', r'\u').encode('unicode-escape').replace(
                        b'\\\\u',
                        b'\\u').decode('unicode-escape') if '%u' in _kk else _kk
                    _hk = HierarchicalKeyword.objects.filter(name__iexact=f'{_kk.strip()}')
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
        label=_('Group'),
        queryset=Group.objects.all(),
        required=False)
    owner = forms.ModelChoiceField(
        label=_('Owner'),
        queryset=get_user_model().objects.all(),
        required=False)
    category = forms.ModelChoiceField(
        label=_('Category'),
        queryset=TopicCategory.objects.all(),
        required=False)
    license = forms.ModelChoiceField(
        label=_('License'),
        queryset=License.objects.all(),
        required=False)
    regions = forms.ModelChoiceField(
        label=_('Regions'),
        queryset=Region.objects.all(),
        required=False)
    date = forms.DateTimeField(
        label=_('Date'),
        required=False)
    language = forms.ChoiceField(
        label=_('Language'),
        required=False,
        choices=LANGUAGES,
    )
    keywords = forms.CharField(required=False)
    ids = forms.CharField(required=False, widget=forms.HiddenInput())


class BatchPermissionsForm(forms.Form):
    group = forms.ModelChoiceField(
        label=_('Group'),
        queryset=Group.objects.all(),
        required=False)
    user = forms.ModelChoiceField(
        label=_('User'),
        queryset=get_user_model().objects.all(),
        required=False)
    permission_type = forms.MultipleChoiceField(
        label=_('Permission Type'),
        required=True,
        widget=forms.CheckboxSelectMultiple,
        choices=(
            ('r', 'Read'),
            ('w', 'Write'),
            ('d', 'Download'),
        ),
    )
    mode = forms.ChoiceField(
        label=_('Mode'),
        required=True,
        widget=forms.RadioSelect,
        choices=(
            ('set', 'Set'),
            ('unset', 'Unset'),
        ),
    )
    ids = forms.CharField(required=False, widget=forms.HiddenInput())


class UserAndGroupPermissionsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(UserAndGroupPermissionsForm, self).__init__(*args, **kwargs)
        self.fields['layers'].label_from_instance = self.label_from_instance

    layers = forms.ModelMultipleChoiceField(
        queryset=Layer.objects.all(),
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
    ids = forms.CharField(required=False, widget=forms.HiddenInput())

    @staticmethod
    def label_from_instance(obj):
        return obj.title


class CuratedThumbnailForm(ModelForm):
    class Meta:
        model = CuratedThumbnail
        fields = ['img']


class OwnerRightsRequestForm(forms.Form):
    resource = forms.ModelChoiceField(
        label=_('Resource'),
        queryset=ResourceBase.objects.all(),
        widget=forms.HiddenInput())
    reason = forms.CharField(
        label=_('Reason'),
        widget=forms.Textarea,
        help_text=_('Short reasoning behind the request'),
        required=True)

    class Meta:
        fields = ['reason', 'resource']
