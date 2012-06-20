from django.contrib.auth.models import User

from geonode import GeoNodeException

def get_default_user():
    """Create a default user
    """
    try:
        return User.objects.get(is_superuser=True)
    except User.DoesNotExist:
        raise GeoNodeException('You must have an admin account configured '
                               'before importing data. '
                               'Try: django-admin.py createsuperuser')
    except User.MultipleObjectsReturned:
        raise GeoNodeException('You have multiple admin accounts, '
                               'please specify which I should use.')


def get_valid_user(user=None):
    """Gets the default user or creates it if it does not exist
    """
    if user is None:
        theuser = get_default_user()
    elif isinstance(user, basestring):
        theuser = User.objects.get(username=user)
    elif user.is_anonymous():
        raise GeoNodeException('The user uploading files must not '
                               'be anonymous')
    else:
        theuser = user

    #FIXME: Pass a user in the unit tests that is not yet saved ;)
    assert isinstance(theuser, User)

    return theuser
