#########################################################################
#
# Copyright (C) 2017 OSGeo
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

import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.template.defaultfilters import slugify
from django.shortcuts import redirect

from .forms import NewLayerForm
from .utils import create_layer


@login_required
def layer_create(request, template='createlayer/layer_create.html'):
    """
    Create an empty layer.
    """
    error = None
    if request.method == 'POST':
        form = NewLayerForm(request.POST)
        if form.is_valid():
            try:
                name = form.cleaned_data['name']
                name = slugify(name.replace(".", "_"))
                title = form.cleaned_data['title']
                geometry_type = form.cleaned_data['geometry_type']
                attributes = form.cleaned_data['attributes']
                permissions = form.cleaned_data["permissions"]
                layer = create_layer(name, title, request.user.username, geometry_type, attributes)
                layer.set_permissions(json.loads(permissions))
                return redirect(layer)
            except Exception as e:
                error = f'{e} ({type(e)})'
    else:
        form = NewLayerForm()

    ctx = {
        'form': form,
        'is_layer': True,
        'error': error,
    }

    return render(request, template, context=ctx)
