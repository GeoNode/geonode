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

from fields import MultiThesauriField
from widgets import MultiThesauriWidget

from autocomplete_light.widgets import ChoiceWidget
from autocomplete_light.contrib.taggit_field import TaggitField, TaggitWidget

from django import forms
from django.core import validators
from django.forms import models
from django.forms.fields import ChoiceField
from django.forms.utils import flatatt
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.db.models import Q

from django.utils.encoding import (
    force_text,
)

from bootstrap3_datetime.widgets import DateTimePicker
from modeltranslation.forms import TranslationModelForm

from geonode.base.models import TopicCategory, Region, License
from geonode.people.models import Profile
from geonode.base.enumerations import ALL_LANGUAGES
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model


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
    except BaseException:
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


class TreeWidget(TaggitWidget):
    input_type = 'text'

    def render(self, name, values, attrs=None):
        if isinstance(values, basestring):
            vals = values
        elif values:
            vals = ','.join([str(i.tag.name) for i in values])
        else:
            vals = ""
        output = ["""<div class="keywords-container"><span class="input-group">
                <input class='form-control'
                       id='id_resource-keywords'
                       name='resource-keywords'
                       value='%s'><br/>""" % (vals)]
        output.append(
            '<div id="treeview" class="" style="display: none"></div>')
        output.append(
            '<span class="input-group-addon" id="treeview-toggle"><i class="fa fa-folder"></i></span>')
        output.append('</span></div>')

        return mark_safe(u'\n'.join(output))


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

    def render(self, name, value, attrs=None):
        if value is None:
            value = []
        final_attrs = self.build_attrs(attrs, name=name)
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
        selected_choices = set(force_text(v) for v in selected_choices)
        output = []

        output.append(format_html('<optgroup label="{}">', 'Global'))
        for option_value, option_label in self.choices:
            if not isinstance(
                    option_label, (list, tuple)) and isinstance(
                    option_label, basestring):
                output.append(
                    self.render_option_value(
                        selected_choices,
                        option_value,
                        option_label))
        output.append('</optgroup>')

        for option_value, option_label in self.choices:
            if isinstance(
                    option_label, (list, tuple)) and not isinstance(
                    option_label, basestring):
                output.append(
                    format_html(
                        '<optgroup label="{}">',
                        force_text(option_value)))
                for option in option_label:
                    if isinstance(
                            option, (list, tuple)) and not isinstance(
                            option, basestring):
                        if isinstance(
                                option[1][0], (list, tuple)) and not isinstance(
                                option[1][0], basestring):
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

        if not ccf_data:
            msg = _("Category is required.")
            self._errors = self.error_class([msg])

        # Always return the full collection of cleaned data.
        return cleaned_data


class TKeywordForm(forms.Form):
    tkeywords = MultiThesauriField(
        label=_("Keywords from Thesauri"),
        required=False,
        help_text=_("List of keywords from Thesauri"),
        widget=MultiThesauriWidget())

    def clean(self):
        cleaned_data = None
        if self.data:
            try:
                cleaned_data = [{key: self.data.getlist(key)} for key, value in self.data.items(
                ) if 'tkeywords-tkeywords' in key.lower() and 'autocomplete' not in key.lower()]
            except BaseException:
                pass

        return cleaned_data


class ResourceBaseForm(TranslationModelForm):
    """Base form for metadata, should be inherited by childres classes of ResourceBase"""

    owner = forms.ModelChoiceField(
        empty_label="Owner",
        label=_("Owner"),
        required=False,
        queryset=Profile.objects.exclude(
            username='AnonymousUser'),
        widget=ChoiceWidget('ProfileAutocomplete'))

    _date_widget_options = {
        "icon_attrs": {"class": "fa fa-calendar"},
        "attrs": {"class": "form-control input-sm"},
        # "format": "%Y-%m-%d %I:%M %p",
        "format": "%Y-%m-%d",
        # Options for the datetimepickers are not set here on purpose.
        # They are set in the metadata_form_js.html template because
        # bootstrap-datetimepicker uses jquery for its initialization
        # and we need to ensure it is available before trying to
        # instantiate a new datetimepicker. This could probably be improved.
        "options": False,
    }
    date = forms.DateTimeField(
        label=_("Date"),
        localize=True,
        input_formats=['%Y-%m-%d'],
        widget=DateTimePicker(**_date_widget_options)
    )
    temporal_extent_start = forms.DateTimeField(
        label=_("temporal extent start"),
        required=False,
        localize=True,
        input_formats=['%Y-%m-%d'],
        widget=DateTimePicker(**_date_widget_options)
    )
    temporal_extent_end = forms.DateTimeField(
        label=_("temporal extent end"),
        required=False,
        localize=True,
        input_formats=['%Y-%m-%d'],
        widget=DateTimePicker(**_date_widget_options)
    )

    poc = forms.ModelChoiceField(
        empty_label=_("Person outside GeoNode (fill form)"),
        label=_("Point of Contact"),
        required=False,
        queryset=Profile.objects.exclude(
            username='AnonymousUser'),
        widget=ChoiceWidget('ProfileAutocomplete'))

    metadata_author = forms.ModelChoiceField(
        empty_label=_("Person outside GeoNode (fill form)"),
        label=_("Metadata Author"),
        required=False,
        queryset=Profile.objects.exclude(
            username='AnonymousUser'),
        widget=ChoiceWidget('ProfileAutocomplete'))

    keywords = TaggitField(
        label=_("Free-text Keywords"),
        required=False,
        help_text=_("A space or comma-separated list of keywords. Use the widget to select from Hierarchical tree."),
        widget=TreeWidget(
            autocomplete='HierarchicalKeywordAutocomplete'))

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
