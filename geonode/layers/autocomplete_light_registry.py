import autocomplete_light
from models import Layer

autocomplete_light.register(
    Layer,
    search_fields=[
        '^title',
        '^typename'],
    autocomplete_js_attributes={
        'placeholder': 'Layer name..',
    },
)
