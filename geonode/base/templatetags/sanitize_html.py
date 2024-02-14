from django import template
from django.conf import settings
import nh3
from django.utils.encoding import force_str

register = template.Library()


@register.filter(name="sanitize_html")
def sanitize_html(value):
    """
    This filter can be used in Django templates to ensure that HTML content is safe to render. It leverages the
    nh3 library (https://github.com/messense/nh3) to remove dangerous tags and JavaScript patterns.

    The allowed HTML tags and attributes can be
    configured via the 'NH3_DEFAULT_CONFIG' setting in Django's settings.py. If this configuration is not set, a default
    set of safe tags will be used.

    Usage in templates: {{ some_variable|sanitize_html|safe }}

    :param value: The HTML content to be sanitized within the template.
    :return: Sanitized HTML content safe for rendering in templates.
    """

    # Tests: Ensure the value is converted to a string if it's a lazy object
    value = force_str(value)

    nh3_config = getattr(
        settings,
        "NH3_DEFAULT_CONFIG",
        {
            "tags": {"b", "a", "img", "p", "ul", "li", "strong", "em", "span"},
        },
    )

    return nh3.clean(value, **nh3_config)
