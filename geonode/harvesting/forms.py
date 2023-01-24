#########################################################################
#
# Copyright (C) 2021 OSGeo
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

from django import forms

from . import models

logger = logging.getLogger(__name__)


class HarvesterForm(forms.ModelForm):
    def clean(self):
        super().clean()
        if self.instance.status != models.Harvester.STATUS_READY:
            raise forms.ValidationError(
                f"Harvester is currently busy. Please wait until current "
                f"status becomes {models.Harvester.STATUS_READY!r} before retrying"
            )
        return self.cleaned_data
