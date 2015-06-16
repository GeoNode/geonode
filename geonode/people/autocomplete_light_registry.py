import autocomplete_light

from .models import Profile


class ProfileAutocomplete(autocomplete_light.AutocompleteModelBase):
    search_fields = [
        '^first_name',
        '^email',
        '^username']

    def choices_for_request(self):
        self.choices = self.choices.exclude(username='AnonymousUser')
        return super(ProfileAutocomplete, self).choices_for_request()


autocomplete_light.register(
    Profile,
    ProfileAutocomplete
)
