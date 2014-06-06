import autocomplete_light
from models import ResourceBase, TopicCategory, Region

autocomplete_light.register(TopicCategory,
    search_fields=['^identifier',  '^description'],
    autocomplete_js_attributes={'placeholder': 'Topic Category ..',},
)

autocomplete_light.register(Region,
    search_fields=['^name'],
    autocomplete_js_attributes={'placeholder': 'Region/Country ..',},
)

autocomplete_light.register(ResourceBase,
    search_fields=['^title'],
    autocomplete_js_attributes={'placeholder': 'Resource name..',},
)
