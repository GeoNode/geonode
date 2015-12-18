# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
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

import autocomplete_light
from autocomplete_light.contrib.taggit_field import TaggitField, TaggitWidget

from django import forms
from django.forms.widgets import TextInput, Widget
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from mptt.forms import TreeNodeMultipleChoiceField
from bootstrap3_datetime.widgets import DateTimePicker
from modeltranslation.forms import TranslationModelForm

from geonode.base.models import TopicCategory, Region
from geonode.people.models import Profile


class CategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return '<span class="has-popover" data-container="body" data-toggle="popover" data-placement="top" ' \
               'data-content="' + obj.description + '" trigger="hover">' + obj.gn_description + '</span>'

class TreeWidget(forms.TextInput):
        input_type = 'text'
        def __init__(self, attrs=None):
            super(TreeWidget, self).__init__(attrs) 

        def render(self, name, values, attrs=None):
            vals = ','.join([str(i.tag.name) for i in values])
            #vals = ""
            output = ["<input class='form-control' id='id_resource-keywords' name='resource-keywords' value='%s'><br/>" % (vals)]
            output.append('<div id="treeview" class=""></div>')
            return mark_safe(u'\n'.join(output))
        

        

class CategoryForm(forms.Form):
    category_choice_field = CategoryChoiceField(required=False,
                                                label='*' + _('Category'),
                                                empty_label=None,
                                                queryset=TopicCategory.objects.extra(order_by=['description']))

    def clean(self):
        cleaned_data = self.data
        ccf_data = cleaned_data.get("category_choice_field")

        if not ccf_data:
            msg = _("Category is required.")
            self._errors = self.error_class([msg])

        # Always return the full collection of cleaned data.
        return cleaned_data


class ResourceBaseForm(TranslationModelForm):
    """Base form for metadata, should be inherited by childres classes of ResourceBase"""

    owner = forms.ModelChoiceField(
        empty_label="Owner",
        label="Owner",
        required=False,
        queryset=Profile.objects.exclude(
            username='AnonymousUser'),
        widget=autocomplete_light.ChoiceWidget('ProfileAutocomplete'))

    _date_widget_options = {
        "icon_attrs": {"class": "fa fa-calendar"},
        "attrs": {"class": "form-control input-sm"},
        "format": "%Y-%m-%d %I:%M %p",
        # Options for the datetimepickers are not set here on purpose.
        # They are set in the metadata_form_js.html template because
        # bootstrap-datetimepicker uses jquery for its initialization
        # and we need to ensure it is available before trying to
        # instantiate a new datetimepicker. This could probably be improved.
        "options": False,
        }
    date = forms.DateTimeField(
        localize=True,
        input_formats=['%Y-%m-%d %I:%M %p'],
        widget=DateTimePicker(**_date_widget_options)
    )
    temporal_extent_start = forms.DateTimeField(
        required=False,
        localize=True,
        input_formats=['%Y-%m-%d %I:%M %p'],
        widget=DateTimePicker(**_date_widget_options)
    )
    temporal_extent_end = forms.DateTimeField(
        required=False,
        localize=True,
        input_formats=['%Y-%m-%d %I:%M %p'],
        widget=DateTimePicker(**_date_widget_options)
    )

    poc = forms.ModelChoiceField(
        empty_label="Person outside GeoNode (fill form)",
        label="Point Of Contact",
        required=False,
        queryset=Profile.objects.exclude(
            username='AnonymousUser'),
        widget=autocomplete_light.ChoiceWidget('ProfileAutocomplete'))

    metadata_author = forms.ModelChoiceField(
        empty_label="Person outside GeoNode (fill form)",
        label="Metadata Author",
        required=False,
        queryset=Profile.objects.exclude(
            username='AnonymousUser'),
        widget=autocomplete_light.ChoiceWidget('ProfileAutocomplete'))

    keywords = TaggitField(required=False, help_text=_("Select keywords from the tree"), widget=TreeWidget())

    #keywords = TaggitField(
    #    required=False,
    #    help_text=_("A space or comma-separated list of keywords"),
    #    widget=TaggitWidget('TagAutocomplete'))

    regions = TreeNodeMultipleChoiceField(
        required=False,
        queryset=Region.objects.all(),
        level_indicator=u'___')
    regions.widget.attrs = {"size": 20}

    def __init__(self, *args, **kwargs):
        super(ResourceBaseForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update(
                    {
                        'class': 'has-popover',
                        'data-content': help_text,
                        'data-placement': 'right',
                        'data-container': 'body',
                        'data-html': 'true'})

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
            'detail_url'
            )
