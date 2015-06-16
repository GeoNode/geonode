from django import template

register = template.Library()


@register.simple_tag
def geogit_statistics_url(layer):
    return getattr(layer.link_set.filter(name__icontains='geogit statistics').first(), 'url', None)


@register.simple_tag
def geogit_log_url(layer):
    return getattr(layer.link_set.filter(name__icontains='geogit log').first(), 'url', None)


@register.simple_tag
def geogit_repo_url(layer):
    return getattr(layer.link_set.filter(name__icontains='clone in geogit').first(), 'url', None)
