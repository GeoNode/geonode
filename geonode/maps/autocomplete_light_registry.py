import autocomplete_light
from models import Contact
from django.contrib.auth.models import User

autocomplete_light.register(User,
    # Just like in ModelAdmin.search_fields
    search_fields=['^username','^email'],
    # This will actually data-minimum-characters which will set
    # widget.autocomplete.minimumCharacters.
    autocomplete_js_attributes={'placeholder': 'name or email..',},
)

# This will generate a PersonAutocomplete class
autocomplete_light.register(Contact,
    # Just like in ModelAdmin.search_fields
    search_fields=['^name',  '^email', '^user__username', '^user__email'],
    # This will actually data-minimum-characters which will set
    # widget.autocomplete.minimumCharacters.
    autocomplete_js_attributes={'placeholder': 'name or email..',},
)

