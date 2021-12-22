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
import json
import logging

from deprecated import deprecated
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from geonode import geoserver  # noqa
from geonode.base.models import ResourceBase
from geonode.client.hooks import hookset
from geonode.layers.models import Dataset, Style
from geonode.utils import check_ogc_backend

logger = logging.getLogger("geonode.maps.models")


class Map(ResourceBase):

    """
    A Map aggregates several layers together and annotates them with a viewport
    configuration.
    """
    last_modified = models.DateTimeField(auto_now_add=True)
    # The last time the map was modified.

    urlsuffix = models.CharField(_("Site URL"), max_length=255, blank=True)
    # Alphanumeric alternative to referencing maps by id, appended to end of
    # URL instead of id, ie http://domain/maps/someview

    featuredurl = models.CharField(_("Featured Map URL"), max_length=255, blank=True)
    # Full URL for featured map view, ie http://domain/someview

    def __str__(self):
        return f'{self.title} by {(self.owner.username if self.owner else "<Anonymous>")}'

    @property
    def datasets(self):
        dataset_names = MapLayer.objects.filter(map__id=self.id).values("name")
        return Dataset.objects.filter(alternate__in=dataset_names) | Dataset.objects.filter(name__in=dataset_names)

    def json(self, dataset_filter):
        """
        Get a JSON representation of this map suitable for sending to geoserver
        for creating a download of all layers
        """
        map_datasets = MapLayer.objects.filter(map=self.id)
        layers = []
        for map_dataset in map_datasets:
            if map_dataset.local:
                layer = Dataset.objects.get(alternate=map_dataset.name)
                layers.append(layer)
            else:
                pass

        if dataset_filter:
            layers = [lyr for lyr in layers if dataset_filter(lyr)]

        # the readme text will appear in a README file in the zip
        readme = f"Title: {self.title}\nAuthor: {self.poc}\nAbstract: {self.abstract}\n"
        if self.license:
            readme += f"License: {self.license}"
            if self.license.url:
                readme += f" ({self.license.url})"
            readme += "\n"
        if self.constraints_other:
            readme += f"Additional constraints: {self.constraints_other}\n"

        def dataset_json(lyr):
            return {
                "name": lyr.alternate,
                "service": lyr.service_type if hasattr(lyr, "service_type") else "",
                "serviceURL": "",
                "metadataURL": "",
            }

        map_config = {
            # the title must be provided and is used for the zip file name
            "map": {"readme": readme, "title": self.title},
            "datasets": [dataset_json(lyr) for lyr in layers],
        }

        return json.dumps(map_config)

    def keyword_list(self):
        keywords_qs = self.keywords.all()
        if keywords_qs:
            return [kw.name for kw in keywords_qs]
        else:
            return []

    def get_absolute_url(self):
        return hookset.map_detail_url(self)

    @property
    def embed_url(self):
        return reverse("map_embed", kwargs={"mapid": self.pk})

    def get_bbox_from_datasets(self, layers):
        """
        Calculate the bbox from a given list of Dataset objects

        bbox format: [xmin, xmax, ymin, ymax]
        """
        bbox = None
        for layer in layers:
            dataset_bbox = layer.bbox
            if bbox is None:
                bbox = list(dataset_bbox[0:4])
            else:
                bbox[0] = min(bbox[0], dataset_bbox[0])
                bbox[1] = max(bbox[1], dataset_bbox[1])
                bbox[2] = min(bbox[2], dataset_bbox[2])
                bbox[3] = max(bbox[3], dataset_bbox[3])

        return bbox

    @property
    def sender(self):
        return None

    @property
    def class_name(self):
        return self.__class__.__name__

    @property
    def is_public(self):
        """
        Returns True if anonymous (public) user can view map.
        """
        from guardian.shortcuts import get_anonymous_user

        user = get_anonymous_user()
        return user.has_perm("base.view_resourcebase", obj=self.resourcebase_ptr)

    @property
    def dataset_group(self):
        """
        Returns layer group name from local OWS for this map instance.
        """
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            from geonode.geoserver.helpers import gs_catalog, ogc_server_settings

            lg_name = f"{slugify(self.title)}_{self.id}"
            try:
                return {"catalog": gs_catalog.get_layergroup(lg_name), "ows": ogc_server_settings.ows}
            except Exception:
                return {"catalog": None, "ows": ogc_server_settings.ows}
        else:
            return None

    @deprecated(version="2.10.1", reason="APIs have been changed on geospatial service")
    def publish_dataset_group(self):
        """
        Publishes local map layers as WMS layer group on local OWS.
        """
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            from geoserver.layergroup import UnsavedLayerGroup as GsUnsavedLayerGroup

            from geonode.geoserver.helpers import gs_catalog
        else:
            raise Exception("Cannot publish layer group if geonode.geoserver is not in INSTALLED_APPS")

        # temporary permission workaround:
        # only allow public maps to be published
        if not self.is_public:
            return "Only public maps can be saved as layer group."

        map_datasets = MapLayer.objects.filter(map=self.id)

        # Local Group Dataset layers and corresponding styles
        layers = []
        lg_styles = []
        for ml in map_datasets:
            if ml.local:
                layer = Dataset.objects.get(alternate=ml.name)
                style = ml.styles or getattr(layer.default_style, "name", "")
                layers.append(layer)
                lg_styles.append(style)
        lg_datasets = [lyr.name for lyr in layers]

        # Group layer bounds and name
        lg_bounds = [str(coord) for coord in self.bbox]
        lg_name = f"{slugify(self.title)}_{self.id}"

        # Update existing or add new group layer
        lg = self.dataset_group
        if lg is None:
            lg = GsUnsavedLayerGroup(gs_catalog, lg_name, lg_datasets, lg_styles, lg_bounds)
        else:
            lg.layers, lg.styles, lg.bounds = lg_datasets, lg_styles, lg_bounds
        gs_catalog.save(lg)
        return lg_name

    class Meta(ResourceBase.Meta):
        pass


class MapLayer(models.Model):

    """
    The MapLayer model represents a layer included in a map.  This doesn't just
    identify the dataset, but also extra options such as which style to load
    and the file format to use for image tiles.
    """

    map = models.ForeignKey(Map, related_name="maplayers", on_delete=models.CASCADE, null=True, blank=True)
    # The map containing this layer

    dataset = models.ForeignKey(Dataset, related_name="maplayers", on_delete=models.SET_NULL, null=True, blank=True)
    # The dataset object, retrieved by the `name` (Dataset alternate) and `store` attributes.

    extra_params = models.JSONField(null=True, default=dict, blank=True)
    # extra_params: an opaque JSONField where the client can put useful
    # information about the maplayer. For the moment the only extra information
    # will be the "msid", which is set by the client to match the maplayer with
    # the layer inside the mapconfig blob.

    name = models.TextField(_("name"), null=True, blank=True)
    # The name of the layer to load.

    store = models.TextField(_("store"), null=True, blank=True)

    # The interpretation of this name depends on the source of the layer (Google
    # has a fixed set of names, WMS services publish a list of available layers
    # in their capabilities documents, etc.)

    current_style = models.TextField(_("current style"), null=True, blank=True)
    # Here in `current_style` we store the selected style.

    ows_url = models.URLField(_("ows URL"), null=True, blank=True)
    # The URL of the OWS service providing this layer, if any exists.

    local = models.BooleanField(default=False, blank=True)
    # True if this layer is served by the local geoserver

    @property
    def dataset_title(self):
        """
            Used by geonode/maps/templates/maps/map_download.html
        """
        if self.dataset:
            title = self.dataset.title
        else:
            title = self.name
        return title

    @property
    def local_link(self):
        """
            Used by geonode/maps/templates/maps/map_download.html
        """
        layer = self.dataset if self.local else None
        if layer:
            link = f'<a href="{layer.get_absolute_url()}">{layer.title}</a>'
        else:
            link = f"<span>{self.name}</span> "
        return link

    @property
    def get_legend(self):
        # Get style name or return None
        if self.dataset and self.dataset.default_style:
            style_name = self.dataset.default_style.name
        elif self.current_style and ":" in self.current_style:
            style_name = self.current_style.split(":")[1]
        elif self.current_style:
            style_name = self.current_style
        else:
            return None

        href = self.dataset.get_legend_url(style_name=style_name)
        style = Style.objects.filter(name=style_name).first()
        if style:
            # replace map-legend display name if style has a title
            style_name = style.sld_title or style_name
        return {style_name: href}

    class Meta:
        ordering = ["-pk"]

    def __str__(self):
        return f"{self.ows_url}?datasets={self.name}"
