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

from django.forms import models

from .models import GeoNodeThemeCustomization


class GeoNodeThemeCustomizationAdminForm(models.ModelForm):
    """
    """

    class Meta:
        """
        """
        model = GeoNodeThemeCustomization
        fields = ('name',
                  'description',
                  'logo',
                  'jumbotron_bg',
                  'jumbotron_welcome_hide',
                  'jumbotron_welcome_title',
                  'jumbotron_welcome_content',
                  'jumbotron_site_description',
                  'body_color',
                  'navbar_color',
                  'jumbotron_color',
                  'copyright_color',
                  'partners_title',
                  'partners',
                  'copyright',
                  'contactus',
                  'contact_name',
                  'contact_position',
                  'contact_administrative_area',
                  'contact_city',
                  'contact_street',
                  'contact_postal_code',
                  'contact_city',
                  'contact_country',
                  'contact_delivery_point',
                  'contact_voice',
                  'contact_facsimile',
                  'contact_email',)

    def clean_logo(self):
        file_img = self.cleaned_data['logo']
        # dump image content locally
        # path = default_storage.save('tmp/' + file_img.name,
        #                             ContentFile(file_img.read()))
        # tmp_file = os.path.join(settings.MEDIA_ROOT, path)

        return file_img

    def clean_jumbotron_bg(self):
        file_img = self.cleaned_data['jumbotron_bg']
        # dump image content locally
        # path = default_storage.save('tmp/' + file_img.name,
        #                             ContentFile(file_img.read()))
        # tmp_file = os.path.join(settings.MEDIA_ROOT, path)

        return file_img
