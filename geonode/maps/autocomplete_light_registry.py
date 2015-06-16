import autocomplete_light
from models import Map

autocomplete_light.register(
    Map,
    search_fields=['^title'],
    autocomplete_js_attributes={
        'placeholder': 'Map name..',
    },
)
