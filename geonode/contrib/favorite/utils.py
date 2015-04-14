from django.core.urlresolvers import reverse
import models


def get_favorite_info(user, content_object):
    """
    return favorite info dict containing:
        a. an add favorite url for the input parameters.
        b. whether there is an existing Favorite for the input parameters.
        c. a delete url (if there is an existing Favorite).
    """
    result = {}

    url_content_type = type(content_object).__name__.lower()
    result["add_url"] = reverse("add_favorite_{}".format(url_content_type), args=[content_object.pk])

    existing_favorite = models.Favorite.objects.favorite_for_user_and_content_object(user, content_object)

    if existing_favorite:
        result["has_favorite"] = "true"
        result["delete_url"] = reverse("delete_favorite", args=[existing_favorite.pk])
    else:
        result["has_favorite"] = "false"

    return result
