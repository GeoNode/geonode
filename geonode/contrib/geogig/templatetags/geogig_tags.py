from django import template

register = template.Library()


@register.simple_tag
def geogig_statistics_url(layer):
    return getattr(layer.link_set.filter(name__icontains='geogig statistics').first(), 'url', None)


@register.simple_tag
def geogig_log_url(layer):
    return getattr(layer.link_set.filter(name__icontains='geogig log').first(), 'url', None)


@register.simple_tag
def geogig_repo_url(layer):
    return getattr(layer.link_set.filter(name__icontains='clone in geogig').first(), 'url', None)
