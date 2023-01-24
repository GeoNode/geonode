#########################################################################
#
# Copyright (C) 2020 OSGeo
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

from geonode.geoapps.models import GeoApp
from geonode.base.forms import ResourceBaseForm, get_tree_data


class GeoAppForm(ResourceBaseForm):
    class Meta(ResourceBaseForm.Meta):
        model = GeoApp
        exclude = ResourceBaseForm.Meta.exclude + ("zoom", "projection", "center_x", "center_y", "data")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["regions"].choices = get_tree_data()
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != "":
                self.fields[field].widget.attrs.update(
                    {
                        "class": "has-external-popover",
                        "data-content": help_text,
                        "placeholder": help_text,
                        "data-placement": "right",
                        "data-container": "body",
                        "data-html": "true",
                    }
                )
