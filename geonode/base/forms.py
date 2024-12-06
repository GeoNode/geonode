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
import html
import json
import logging

from django.db.models.query import QuerySet
from bootstrap3_datetime.widgets import DateTimePicker
from dal import autocomplete
import dal.forward
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import validators
from django.db.models import Prefetch, Q
from django.forms import models
from django.forms.fields import ChoiceField, MultipleChoiceField
from django.forms.utils import flatatt
from django.utils.encoding import force_str
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from modeltranslation.forms import TranslationModelForm
from taggit.forms import TagField
from tinymce.widgets import TinyMCE
from django.contrib.admin.utils import flatten
from django.utils.translation import get_language

from geonode.base.enumerations import ALL_LANGUAGES
from geonode.base.models import (
    HierarchicalKeyword,
    License,
    LinkedResource,
    Region,
    ResourceBase,
    Thesaurus,
    ThesaurusKeyword,
    ThesaurusKeywordLabel,
    ThesaurusLabel,
    TopicCategory,
)
from geonode.base.widgets import TaggitSelect2Custom, TaggitProfileSelect2Custom
from geonode.base.fields import MultiThesauriField
from geonode.documents.models import Document
from geonode.layers.models import Dataset
from geonode.base.utils import validate_extra_metadata, remove_country_from_languagecode
from geonode.people import Roles

logger = logging.getLogger(__name__)


def get_tree_data():
    def rectree(parent, path):
        children_list_of_tuples = list()
        c = Region.objects.filter(parent=parent)
        for child in c:
            children_list_of_tuples.append(tuple((path + parent.name, tuple((child.id, child.name)))))
            childrens = rectree(child, f"{parent.name}/")
            if childrens:
                children_list_of_tuples.extend(childrens)

        return children_list_of_tuples

    data = list()
    try:
        t = Region.objects.filter(Q(level=0) | Q(parent=None))
        for toplevel in t:
            data.append(tuple((toplevel.id, toplevel.name)))
            childrens = rectree(toplevel, "")
            if childrens:
                data.append(tuple((toplevel.name, childrens)))
    except Exception:
        pass

    return tuple(data)


class AdvancedModelChoiceIterator(models.ModelChoiceIterator):
    def choice(self, obj):
        return (self.field.prepare_value(obj), self.field.label_from_instance(obj), obj)


class CategoryChoiceField(forms.ModelChoiceField):
    def _get_choices(self):
        if hasattr(self, "_choices"):
            return self._choices

        return AdvancedModelChoiceIterator(self)

    choices = property(_get_choices, ChoiceField._set_choices)

    def label_from_instance(self, obj):
        return (
            '<i class="fa ' + obj.fa_class + ' fa-2x unchecked"></i>'
            '<i class="fa ' + obj.fa_class + ' fa-2x checked"></i>'
            '<span class="has-popover" data-container="body" data-toggle="popover" data-placement="top" '
            'data-content="' + obj.description + '" trigger="hover">'
            "<br/><strong>" + obj.gn_description + "</strong></span>"
        )


class RegionsMultipleChoiceField(forms.MultipleChoiceField):
    def validate(self, value):
        """
        Validates that the input is a list or tuple.
        """
        if self.required and not value:
            raise forms.ValidationError(self.error_messages["required"], code="required")


class RegionsSelect(forms.Select):
    allow_multiple_selected = True

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = []
        final_attrs = self.build_attrs(attrs)
        final_attrs["name"] = name
        output = [format_html('<select multiple="multiple"{}>', flatatt(final_attrs))]
        options = self.render_options(value)
        if options:
            output.append(options)
        output.append("</select>")
        return mark_safe("\n".join(output))

    def value_from_datadict(self, data, files, name):
        try:
            getter = data.getlist
        except AttributeError:
            getter = data.get
        return getter(name)

    def render_option_value(self, selected_choices, option_value, option_label, data_section=None):
        if option_value is None:
            option_value = ""
        option_value = force_str(option_value)
        if option_value in selected_choices:
            selected_html = mark_safe(" selected")
            if not self.allow_multiple_selected:
                # Only allow for a single selection.
                selected_choices.remove(option_value)
        else:
            selected_html = ""

        label = force_str(option_label)

        if data_section is None:
            data_section = ""
        else:
            data_section = force_str(data_section)
            if "/" in data_section:
                label = format_html("{} [{}]", label, data_section.rsplit("/", 1)[1])

        return format_html(
            '<option data-section="{}" value="{}"{}>{}</option>', data_section, option_value, selected_html, label
        )

    def render_options(self, selected_choices):
        # Normalize to strings.
        def _region_id_from_choice(choice):
            if isinstance(choice, int) or (isinstance(choice, str) and choice.isdigit()):
                return int(choice)
            else:
                return choice.id

        selected_choices = {force_str(_region_id_from_choice(v)) for v in selected_choices}
        output = []

        output.append(format_html('<optgroup label="{}">', "Global"))
        for option_value, option_label in self.choices:
            if not isinstance(option_label, (list, tuple)) and isinstance(option_label, str):
                output.append(self.render_option_value(selected_choices, option_value, option_label))
        output.append("</optgroup>")

        for option_value, option_label in self.choices:
            if isinstance(option_label, (list, tuple)) and not isinstance(option_label, str):
                output.append(format_html('<optgroup label="{}">', force_str(option_value)))
                for option in option_label:
                    if isinstance(option, (list, tuple)) and not isinstance(option, str):
                        if isinstance(option[1][0], (list, tuple)) and not isinstance(option[1][0], str):
                            for option_child in option[1][0]:
                                output.append(
                                    self.render_option_value(
                                        selected_choices, *option_child, data_section=force_str(option[1][0][0])
                                    )
                                )
                        else:
                            output.append(
                                self.render_option_value(
                                    selected_choices, *option[1], data_section=force_str(option[0])
                                )
                            )
                    else:
                        output.append(
                            self.render_option_value(selected_choices, *option, data_section=force_str(option_value))
                        )
                output.append("</optgroup>")

        return "\n".join(output)


class CategoryForm(forms.Form):
    category_choice_field = CategoryChoiceField(
        required=False,
        label=f"*{_('Category')}",
        empty_label=None,
        queryset=TopicCategory.objects.filter(is_choice=True).extra(order_by=["description"]),
    )

    def clean(self):
        cleaned_data = self.data
        ccf_data = cleaned_data.get("category_choice_field")
        category_mandatory = getattr(settings, "TOPICCATEGORY_MANDATORY", False)
        if category_mandatory and not ccf_data:
            msg = _("Category is required.")
            self._errors = self.error_class([msg])

        # Always return the full collection of cleaned data.
        return cleaned_data


class TKeywordForm(forms.ModelForm):
    prefix = "tkeywords"

    class Meta:
        model = Document
        fields = ["tkeywords"]

    tkeywords = MultiThesauriField(
        queryset=ThesaurusKeyword.objects.prefetch_related(
            Prefetch("keyword", queryset=ThesaurusKeywordLabel.objects.filter(lang="en"))
        ),
        widget=autocomplete.ModelSelect2Multiple(
            url="thesaurus_autocomplete",
        ),
        label=_("Keywords from Thesaurus"),
        required=False,
        help_text=_(
            "List of keywords from Thesaurus",
        ),
    )


THESAURUS_RESULT_LIST_SEPERATOR = ("", "-------")


class ThesaurusAvailableForm(forms.Form):
    # seperator at beginning of thesaurus search result and between
    # results found in local language and alt label

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lang = get_language()
        for item in Thesaurus.objects.all().order_by("order", "id"):
            tname = self._get_thesauro_title_label(item, lang)
            if item.card_max == 0:
                continue
            elif item.card_max == 1 and item.card_min == 0:
                self.fields[f"{item.id}"] = self._define_choicefield(item, False, tname, lang)
            elif item.card_max == 1 and item.card_min == 1:
                self.fields[f"{item.id}"] = self._define_choicefield(item, True, tname, lang)
            elif item.card_max == -1 and item.card_min == 0:
                self.fields[f"{item.id}"] = self._define_multifield(item, False, tname, lang)
            elif item.card_max == -1 and item.card_min == 1:
                self.fields[f"{item.id}"] = self._define_multifield(item, True, tname, lang)

    def cleanx(self, x):
        cleaned_values = []
        for key, value in x.items():
            if isinstance(value, QuerySet):
                for y in value:
                    cleaned_values.append(y.id)
            elif value:
                cleaned_values.append(value)
        return ThesaurusKeyword.objects.filter(id__in=flatten(cleaned_values))

    def _define_multifield(self, item, required, tname, lang):
        return MultipleChoiceField(
            choices=self._get_thesauro_keyword_label(item, lang),
            widget=autocomplete.Select2Multiple(
                url=f"/base/thesaurus_available/?sysid={item.id}&lang={lang}",
                attrs={"class": "treq" if required else ""},
            ),
            label=f"{tname}",
            required=False,
        )

    def _define_choicefield(self, item, required, tname, lang):
        return models.ChoiceField(
            label=f"{tname}",
            required=False,
            widget=forms.Select(attrs={"class": "treq" if required else ""}),
            choices=self._get_thesauro_keyword_label(item, lang),
        )

    @staticmethod
    def _get_thesauro_keyword_label(item, lang):
        keyword_id_for_given_thesaurus = ThesaurusKeyword.objects.filter(thesaurus_id=item)

        # try find results found for given language e.g. (en-us) if no results found remove country code from language to (en) and try again
        qs_keyword_ids = ThesaurusKeywordLabel.objects.filter(
            lang=lang, keyword_id__in=keyword_id_for_given_thesaurus
        ).values("keyword_id")
        if len(qs_keyword_ids) == 0:
            lang = remove_country_from_languagecode(lang)
            qs_keyword_ids = ThesaurusKeywordLabel.objects.filter(
                lang=lang, keyword_id__in=keyword_id_for_given_thesaurus
            ).values("keyword_id")

        not_qs_ids = (
            ThesaurusKeywordLabel.objects.exclude(keyword_id__in=qs_keyword_ids)
            .order_by("keyword_id")
            .distinct("keyword_id")
            .values("keyword_id")
        )

        qs_local = list(
            ThesaurusKeywordLabel.objects.filter(lang=lang, keyword_id__in=keyword_id_for_given_thesaurus).values_list(
                "keyword_id", "label"
            )
        )
        qs_non_local = list(keyword_id_for_given_thesaurus.filter(id__in=not_qs_ids).values_list("id", "alt_label"))

        return [THESAURUS_RESULT_LIST_SEPERATOR] + qs_local + [THESAURUS_RESULT_LIST_SEPERATOR] + qs_non_local

    @staticmethod
    def _get_thesauro_title_label(item, lang):
        lang = remove_country_from_languagecode(lang)
        tname = ThesaurusLabel.objects.values_list("label", flat=True).filter(thesaurus=item).filter(lang=lang)
        if not tname:
            return Thesaurus.objects.get(id=item.id).title
        return tname.first()


class ContactRoleMultipleChoiceField(forms.ModelMultipleChoiceField):
    def clean(self, value) -> QuerySet:
        try:
            users = get_user_model().objects.filter(username__in=value)
        except TypeError:
            # value of not supported type ...
            raise forms.ValidationError(_("Something went wrong in finding the profile(s) in a contact role form ..."))
        return users


class LinkedResourceForm(forms.ModelForm):
    linked_resources = forms.ModelMultipleChoiceField(
        label=_("Related resources"),
        required=False,
        queryset=None,
        widget=autocomplete.ModelSelect2Multiple(url="autocomplete_linked_resource"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # this is used to automatically validate the POSTed back values
        self.fields["linked_resources"].queryset = ResourceBase.objects.exclude(pk=self.instance.id)
        # these are the LinkedResource already linked to this resource
        self.fields["linked_resources"].initial = LinkedResource.get_target_ids(self.instance).all()
        # this is used by the autocomplete view to exclude current resource
        self.fields["linked_resources"].widget.forward.append(
            dal.forward.Const(
                self.instance.id,
                "exclude",
            )
        )

    class Meta:
        model = ResourceBase
        fields = ["linked_resources"]

    def save_linked_resources(self, links_field="linked_resources"):
        # create and fetch desired links
        target_ids = []
        for res in self.cleaned_data[links_field]:
            LinkedResource.objects.get_or_create(source=self.instance, target=res, internal=False)
            target_ids.append(res.pk)

        # delete remaining links
        (
            LinkedResource.objects.filter(source_id=self.instance.id, internal=False)
            .exclude(target_id__in=target_ids)
            .delete()
        )


class ResourceBaseDateTimePicker(DateTimePicker):
    def build_attrs(self, base_attrs=None, extra_attrs=None, **kwargs):
        "Helper function for building an attribute dictionary."
        if extra_attrs:
            base_attrs.update(extra_attrs)
        base_attrs.update(kwargs)
        return super().build_attrs(base_attrs)
        # return base_attrs


class ResourceBaseForm(TranslationModelForm, LinkedResourceForm):
    """Base form for metadata, should be inherited by childres classes of ResourceBase"""

    abstract = forms.CharField(label=_("Abstract"), required=False, widget=TinyMCE())

    purpose = forms.CharField(label=_("Purpose"), required=False, widget=TinyMCE())

    constraints_other = forms.CharField(label=_("Other constraints"), required=False, widget=TinyMCE())

    supplemental_information = forms.CharField(label=_("Supplemental information"), required=False, widget=TinyMCE())

    ptype = forms.CharField(required=False)
    sourcetype = forms.CharField(required=False)

    data_quality_statement = forms.CharField(label=_("Data quality statement"), required=False, widget=TinyMCE())

    owner = forms.ModelChoiceField(
        empty_label=_(Roles.OWNER.label),
        label=_(Roles.OWNER.label),
        required=True,
        queryset=get_user_model().objects.exclude(username="AnonymousUser"),
        widget=autocomplete.ModelSelect2(url="autocomplete_profile"),
    )

    date = forms.DateTimeField(
        label=_("Date"),
        localize=True,
        input_formats=["%Y-%m-%d %H:%M %p"],
        widget=ResourceBaseDateTimePicker(options={"format": "YYYY-MM-DD HH:mm a"}),
    )

    temporal_extent_start = forms.DateTimeField(
        label=_("temporal extent start"),
        required=False,
        localize=True,
        input_formats=["%Y-%m-%d %H:%M %p"],
        widget=ResourceBaseDateTimePicker(options={"format": "YYYY-MM-DD HH:mm a"}),
    )

    temporal_extent_end = forms.DateTimeField(
        label=_("temporal extent end"),
        required=False,
        localize=True,
        input_formats=["%Y-%m-%d %H:%M %p"],
        widget=ResourceBaseDateTimePicker(options={"format": "YYYY-MM-DD HH:mm a"}),
    )

    metadata_author = ContactRoleMultipleChoiceField(
        label=_(Roles.METADATA_AUTHOR.label),
        required=Roles.METADATA_AUTHOR.is_required,
        queryset=get_user_model().objects.exclude(username="AnonymousUser"),
        widget=TaggitProfileSelect2Custom(url="autocomplete_profile"),
    )

    processor = ContactRoleMultipleChoiceField(
        label=_(Roles.PROCESSOR.label),
        required=Roles.PROCESSOR.is_required,
        queryset=get_user_model().objects.exclude(username="AnonymousUser"),
        widget=TaggitProfileSelect2Custom(url="autocomplete_profile"),
    )

    publisher = ContactRoleMultipleChoiceField(
        label=_(Roles.PUBLISHER.label),
        required=Roles.PUBLISHER.is_required,
        queryset=get_user_model().objects.exclude(username="AnonymousUser"),
        widget=TaggitProfileSelect2Custom(url="autocomplete_profile"),
    )

    custodian = ContactRoleMultipleChoiceField(
        label=_(Roles.CUSTODIAN.label),
        required=Roles.CUSTODIAN.is_required,
        queryset=get_user_model().objects.exclude(username="AnonymousUser"),
        widget=TaggitProfileSelect2Custom(url="autocomplete_profile"),
    )

    poc = ContactRoleMultipleChoiceField(
        label=_(Roles.POC.label),
        required=Roles.POC.is_required,
        queryset=get_user_model().objects.exclude(username="AnonymousUser"),
        widget=TaggitProfileSelect2Custom(url="autocomplete_profile"),
    )

    distributor = ContactRoleMultipleChoiceField(
        label=_(Roles.DISTRIBUTOR.label),
        required=Roles.DISTRIBUTOR.is_required,
        queryset=get_user_model().objects.exclude(username="AnonymousUser"),
        widget=TaggitProfileSelect2Custom(url="autocomplete_profile"),
    )

    resource_user = ContactRoleMultipleChoiceField(
        label=_(Roles.RESOURCE_USER.label),
        required=Roles.RESOURCE_USER.is_required,
        queryset=get_user_model().objects.exclude(username="AnonymousUser"),
        widget=TaggitProfileSelect2Custom(url="autocomplete_profile"),
    )

    resource_provider = ContactRoleMultipleChoiceField(
        label=_(Roles.RESOURCE_PROVIDER.label),
        required=Roles.RESOURCE_PROVIDER.is_required,
        queryset=get_user_model().objects.exclude(username="AnonymousUser"),
        widget=TaggitProfileSelect2Custom(url="autocomplete_profile"),
    )

    originator = ContactRoleMultipleChoiceField(
        label=_(Roles.ORIGINATOR.label),
        required=Roles.ORIGINATOR.is_required,
        queryset=get_user_model().objects.exclude(username="AnonymousUser"),
        widget=TaggitProfileSelect2Custom(url="autocomplete_profile"),
    )

    principal_investigator = ContactRoleMultipleChoiceField(
        label=_(Roles.PRINCIPAL_INVESTIGATOR.label),
        required=Roles.PRINCIPAL_INVESTIGATOR.is_required,
        queryset=get_user_model().objects.exclude(username="AnonymousUser"),
        widget=TaggitProfileSelect2Custom(url="autocomplete_profile"),
    )

    keywords = TagField(
        label=_("Free-text Keywords"),
        required=False,
        help_text=_("A space or comma-separated list of keywords. Use the widget to select from Hierarchical tree."),
        # widget=TreeWidget(url='autocomplete_hierachical_keyword'), #Needs updating to work with select2
        widget=TaggitSelect2Custom(url="autocomplete_hierachical_keyword"),
    )

    regions = RegionsMultipleChoiceField(label=_("Regions"), required=False, widget=RegionsSelect)

    regions.widget.attrs = {"size": 20}

    extra_metadata = forms.CharField(
        required=False,
        widget=forms.Textarea,
        help_text=_(
            'Additional metadata, must be in format [\
                {"metadata_key": "metadata_value"},\
                {"metadata_key": "metadata_value"} \
            ]'
        ),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["regions"].choices = get_tree_data()
        self.can_change_perms = self.user and self.user.has_perm(
            "change_resourcebase_permissions", self.instance.get_self_resource()
        )
        if self.instance and self.instance.id and self.instance.metadata.exists():
            self.fields["extra_metadata"].initial = [x.metadata for x in self.instance.metadata.all()]

        for field in self.fields:
            if field == "featured" and self.user and not self.user.is_superuser:
                self.fields[field].disabled = True
            help_text = self.fields[field].help_text
            if help_text != "":
                self.fields[field].widget.attrs.update(
                    {
                        "class": "has-popover",
                        "data-content": help_text,
                        "data-placement": "right",
                        "data-container": "body",
                        "data-html": "true",
                    }
                )

            if field in ["owner"] and not self.can_change_perms:
                self.fields[field].disabled = True

    def disable_keywords_widget_for_non_superuser(self, user):
        if settings.FREETEXT_KEYWORDS_READONLY and not user.is_superuser:
            self["keywords"].field.disabled = True

    def clean_keywords(self):
        keywords = self.cleaned_data["keywords"]
        _unsescaped_kwds = []
        for k in keywords:
            _k = ("%s" % re.sub(r"%([A-Z0-9]{2})", r"&#x\g<1>;", k.strip())).split(",")
            if not isinstance(_k, str):
                for _kk in [html.unescape(x.strip()) for x in _k]:
                    # Simulate JS Unescape
                    _kk = (
                        _kk.replace("%u", r"\u")
                        .encode("unicode-escape")
                        .replace(b"\\\\u", b"\\u")
                        .decode("unicode-escape")
                        if "%u" in _kk
                        else _kk
                    )
                    _hk = HierarchicalKeyword.objects.filter(name__iexact=f"{_kk.strip()}")
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

    def clean_title(self):
        title = self.cleaned_data.get("title", None)
        if title:
            title = title.replace(",", "_")
        return title

    def clean_extra_metadata(self):
        cleaned_data = self.cleaned_data.get("extra_metadata", [])
        return json.dumps(validate_extra_metadata(cleaned_data, self.instance), indent=4)

    class Meta:
        model = ResourceBase

        exclude = (
            "contacts",
            "name",
            "uuid",
            "bbox_polygon",
            "ll_bbox_polygon",
            "srid",
            "category",
            "csw_typename",
            "csw_schema",
            "csw_mdsource",
            "csw_type",
            "csw_wkt_geometry",
            "metadata_uploaded",
            "metadata_xml",
            "csw_anytext",
            "popular_count",
            "share_count",
            "thumbnail",
            "charset",
            "rating",
            "detail_url",
            "tkeywords",
            "users_geolimits",
            "groups_geolimits",
            "dirty_state",
            "state",
            "blob",
            "files",
            "was_approved",
            "was_published",
        )


class ValuesListField(forms.Field):
    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return []

        value = [item.strip() for item in value.split(",") if item.strip()]

        return value

    def clean(self, value):
        value = self.to_python(value)
        self.validate(value)
        self.run_validators(value)
        return value


class BatchEditForm(forms.Form):
    LANGUAGES = (("", "--------"),) + ALL_LANGUAGES
    group = forms.ModelChoiceField(label=_("Group"), queryset=Group.objects.all(), required=False)
    owner = forms.ModelChoiceField(label=_("Owner"), queryset=get_user_model().objects.all(), required=False)
    category = forms.ModelChoiceField(label=_("Category"), queryset=TopicCategory.objects.all(), required=False)
    license = forms.ModelChoiceField(label=_("License"), queryset=License.objects.all(), required=False)
    regions = forms.ModelChoiceField(label=_("Regions"), queryset=Region.objects.all(), required=False)
    date = forms.DateTimeField(label=_("Date"), required=False)
    language = forms.ChoiceField(
        label=_("Language"),
        required=False,
        choices=LANGUAGES,
    )
    keywords = forms.CharField(required=False)
    ids = forms.CharField(required=False, widget=forms.HiddenInput())


def get_user_choices():
    try:
        return [(x.pk, x.title) for x in Dataset.objects.all().order_by("id")]
    except Exception:
        return []


class UserAndGroupPermissionsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["layers"].label_from_instance = self.label_from_instance

    layers = MultipleChoiceField(
        choices=get_user_choices,
        widget=autocomplete.Select2Multiple(url="datasets_autocomplete"),
        label="Datasets",
        required=False,
    )

    permission_type = forms.ChoiceField(
        required=True,
        widget=forms.RadioSelect,
        choices=(
            ("view", "View"),
            ("download", "Download"),
            ("edit", "Edit"),
        ),
    )
    mode = forms.ChoiceField(
        required=True,
        widget=forms.RadioSelect,
        choices=(
            ("set", "Set"),
            ("unset", "Unset"),
        ),
    )
    ids = forms.CharField(required=False, widget=forms.HiddenInput())

    @staticmethod
    def label_from_instance(obj):
        return obj.title


class OwnerRightsRequestForm(forms.Form):
    resource = forms.ModelChoiceField(
        label=_("Resource"), queryset=ResourceBase.objects.all(), widget=forms.HiddenInput()
    )
    reason = forms.CharField(
        label=_("Reason"), widget=forms.Textarea, help_text=_("Short reasoning behind the request"), required=True
    )

    class Meta:
        fields = ["reason", "resource"]


class ThesaurusImportForm(forms.Form):
    rdf_file = forms.FileField()
