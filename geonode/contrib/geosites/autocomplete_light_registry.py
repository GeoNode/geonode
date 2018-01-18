
from autocomplete_light.registry import register
from geonode.contrib.geosites.utils import resources_for_site
from geonode.base.autocomplete_light_registry import ResourceBaseAutocomplete

class ResourceBaseAutocomplete(ResourceBaseAutocomplete):
   def  choices_for_request(self):
         
         self.choices= self.choices.filter(id__in=resources_for_site())
         return super(ResourceBaseAutocomplete, self).choices_for_request()


register(ResourceBaseAutocomplete,
         search_fields=['title'],
         order_by=['title'],
         limit_choices=100,
         autocomplete_js_attributes={'placeholder': 'Resource name..', },)
