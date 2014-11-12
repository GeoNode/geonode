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

import taggit
from django import forms

from mptt.forms import TreeNodeMultipleChoiceField
from bootstrap3_datetime.widgets import DateTimePicker

from geonode.maps.models import Map
from geonode.people.models import Profile
from django.utils.translation import ugettext_lazy as _
from modeltranslation.forms import TranslationModelForm

from geonode.base.models import Region

import autocomplete_light


class MapForm(TranslationModelForm):
    _date_widget_options = {
        "icon_attrs": {"class": "fa fa-calendar"},
        "attrs": {"class": "form-control input-sm"},
        "format": "%Y-%m-%d %H:%M",
        # Options for the datetimepickers are not set here on purpose.
        # They are set in the metadata_form_js.html template because
        # bootstrap-datetimepicker uses jquery for its initialization
        # and we need to ensure it is available before trying to
        # instantiate a new datetimepicker. This could probably be improved.
        "options": False,
        }
    date = forms.DateTimeField(
        localize=True,
        widget=DateTimePicker(**_date_widget_options)
    )
    temporal_extent_start = forms.DateTimeField(
        required=False,
        localize=True,
        widget=DateTimePicker(**_date_widget_options)
    )
    temporal_extent_end = forms.DateTimeField(
        required=False,
        localize=True,
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

    keywords = taggit.forms.TagField(
        required=False,
        help_text=_("A space or comma-separated list of keywords"))

    regions = TreeNodeMultipleChoiceField(
        required=False,
        queryset=Region.objects.all(),
        level_indicator=u'___')
    regions.widget.attrs = {"size": 20}

    class Meta:
        model = Map
        exclude = (
            'contacts',
            'zoom',
            'projection',
            'center_x',
            'center_y',
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
            'thumbnail')
        widgets = autocomplete_light.get_widgets_dict(Map)
        widgets['abstract'] = forms.Textarea(attrs={'cols': 40, 'rows': 10})

    def __init__(self, *args, **kwargs):
        super(MapForm, self).__init__(*args, **kwargs)
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
