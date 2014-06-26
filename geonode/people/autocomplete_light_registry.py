import autocomplete_light
from models import Profile 
from django.contrib.auth.models import User

autocomplete_light.register(Profile,
    search_fields=['^first_name',  '^email', '^username'],
    autocomplete_js_attributes={'placeholder': 'name or email..',},
)
