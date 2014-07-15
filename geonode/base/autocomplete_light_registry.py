import autocomplete_light
from models import ResourceBase, Region

autocomplete_light.register(Region,
                            search_fields=['^name'],
                            autocomplete_js_attributes={'placeholder': 'Region/Country ..', },)

autocomplete_light.register(ResourceBase,
                            search_fields=['^title'],
                            autocomplete_js_attributes={'placeholder': 'Resource name..', },)
