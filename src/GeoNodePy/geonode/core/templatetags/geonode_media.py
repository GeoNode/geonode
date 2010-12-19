from django import template
from django.conf import settings

register = template.Library()

@register.tag('geonode_media')
def geonode_media(parser, token):
    try:
        tagname, argument = token.split_contents()
        argument = argument[1:-1] # get rid of quotes
        if not argument in settings.MEDIA_LOCATIONS:
            raise template.TemplateSyntaxError, '%s is not a valid resource name' % argument
        return MediaNode(argument)
    except ValueError:
        raise template.TemplateSyntaxError, '%r requires a single argument' % token.contents.split()[0]

class MediaNode(template.Node):
    def __init__(self, resource):
        self.resource = resource

    def render(self, context):
        return settings.STATIC_URL + settings.MEDIA_LOCATIONS[self.resource]
