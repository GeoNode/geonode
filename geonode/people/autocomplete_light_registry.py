import autocomplete_light
from models import Profile 
from django.contrib.auth.models import User

autocomplete_light.register(User,
    search_fields=['^username','^email'],
    autocomplete_js_attributes={'placeholder': 'name or email..',},
)

autocomplete_light.register(Profile,
    search_fields=['^name',  '^email', '^user__username', '^user__email'],
    autocomplete_js_attributes={'placeholder': 'name or email..',},
)
