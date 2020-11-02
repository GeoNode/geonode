"""Template tags for the ``frequently`` app."""
from django import template

from ..models import EntryCategory

register = template.Library()


@register.inclusion_tag('frequently/partials/category.html')
def render_category(slug):
    """Template tag to render a category with all it's entries."""
    try:
        category = EntryCategory.objects.get(slug=slug)
    except EntryCategory.DoesNotExist:
        pass
    else:
        return {'category': category}
    return {}
