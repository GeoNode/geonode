
from autocomplete_light.registry import register
from geonode.contrib.geosites.utils import resources_for_site
from geonode.base.autocomplete_light_registry import ResourceBaseAutocomplete
from geonode.layers.autocomplete_light_registry import LayerAutocomplete
from geonode.maps.autocomplete_light_registry import MapAutocomplete
from geonode.documents.autocomplete_light_registry import DocumentAutocomplete
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document


class ResourceBaseAutocomplete(ResourceBaseAutocomplete):
    def choices_for_request(self):

        self.choices = self.choices.filter(id__in=resources_for_site())
        return super(ResourceBaseAutocomplete, self).choices_for_request()


register(ResourceBaseAutocomplete,
         search_fields=['title'],
         order_by=['title'],
         limit_choices=100,
         autocomplete_js_attributes={'placeholder': 'Resource name..', },)


class DocumentAutocomplete(DocumentAutocomplete):
    def choices_for_request(self):
        self.choices = Document.objects.filter(id__in=resources_for_site)
        return super(DocumentAutocomplete, self).choices_for_request()


register(DocumentAutocomplete,
         search_fields=['title'],
         order_by=['title'],
         limit_choices=100,
         autocomplete_js_attributes={
             'placeholder': 'Document name..',
         },
         )


class LayerAutocomplete(LayerAutocomplete):
    def choices_for_request(self):
        self.choices = Layer.objects.filter(id__in=resources_for_site)
        return super(LayerAutocomplete, self).choices_for_request()


register(LayerAutocomplete,
         search_fields=[
             'title',
             '^alternate'],
         order_by=['title'],
         limit_choices=100,
         autocomplete_js_attributes={
             'placeholder': 'Layer name..',
         })


class MapAutocomplete(MapAutocomplete):
    def choices_for_request(self):
        self.choices = Map.objects.filter(id__in=resources_for_site)
        return super(MapAutocomplete, self).choices_for_request()


register(MapAutocomplete,
         search_fields=['title'],
         order_by=['title'],
         limit_choices=100,
         autocomplete_js_attributes={
             'placeholder': 'Map name..',
         })
