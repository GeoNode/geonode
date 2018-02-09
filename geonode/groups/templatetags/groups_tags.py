from django import template
from django.contrib.staticfiles.storage import staticfiles_storage

register = template.Library()


@register.simple_tag
def group_profile_image(group_profile, css_classes="", size=None):
    """Returns an HTML img tag with the input group_profiles's logo.

    If the group profile does not have an associated logo, a stock image is
    used.

    """

    if isinstance(css_classes, basestring):
        class_attr = 'class="{}" '.format(css_classes)
    else:
        try:
            class_attr = 'class="{}" '.format(
                " ".join(str(i) for i in css_classes))
        except Exception:
            class_attr = ""
    if size is not None:
        style_attr = 'style="width: {size}px; height: {size}px" '.format(
            size=size)
    else:
        style_attr = ""

    if group_profile.logo.name:
        url = group_profile.logo.url
    else:
        url = staticfiles_storage.url("geonode/img/default-avatar.jpg")
    img_tag = '<img {css}{style}src="{url}" alt="{alt}">'.format(
        css=class_attr,
        style=style_attr,
        url=url,
        alt=group_profile.title,
    )
    return img_tag
