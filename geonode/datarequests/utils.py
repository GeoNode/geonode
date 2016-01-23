import random
import string

from django.core.exceptions import ObjectDoesNotExist

from geonode.people.models import Profile


def create_login_credentials(data_request):

    first_name = data_request.first_name
    first_name_f = ""
    for i in first_name.lower().split():
        first_name_f += i[0]

    middle_name_f = "".join(data_request.middle_name.split())
    last_name_f = "".join(data_request.last_name.split())

    base_username = (first_name_f + middle_name_f + last_name_f).lower()

    unique = False
    counter = 0
    final_username = base_username
    while not unique:
        if counter > 0:
            final_username = final_username + str(counter)

        try:
            Profile.objects.get(
                username=final_username,
            )
            counter += 1

        except ObjectDoesNotExist:
            unique = True

    # Generate random password
    password = ''
    for i in range(16):
        password += random.choice(string.lowercase + string.uppercase + string.digits)

    return final_username, password
