# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2018 OSGeo
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

from django import forms
from django.contrib import admin

from .models import Partner, GeoNodeThemeCustomization


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'title', 'href',)


class GeonodeThemCustomizationForm(forms.ModelForm):
    class Meta:
        model = GeoNodeThemeCustomization
        widgets = {
            'body_color': forms.TextInput(attrs={'type': 'color'}),
            'navbar_color': forms.TextInput(attrs={'type': 'color'}),
            'jumbotron_color': forms.TextInput(attrs={'type': 'color'}),
            'copyright_color': forms.TextInput(attrs={'type': 'color'}),
        }
        fields = '__all__'


@admin.register(GeoNodeThemeCustomization)
class GeoNodeThemeCustomizationAdmin(admin.ModelAdmin):
    form = GeonodeThemCustomizationForm
    list_display = ('id', 'is_enabled', 'name', 'date', 'description')
    list_display_links = ('id', 'name',)
