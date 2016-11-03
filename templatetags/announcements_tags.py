from django import template
from django.db.models import Q
from django.utils import timezone

from announcements.models import Announcement


register = template.Library()


class AnnouncementsNode(template.Node):
    
    @classmethod
    def handle_token(cls, parser, token):
        bits = token.split_contents()
        if len(bits) != 3:
            raise template.TemplateSyntaxError
        return cls(as_var=bits[2])
    
    def __init__(self, as_var):
        self.as_var = as_var
    
    def render(self, context):
        request = context["request"]
        qs = Announcement.objects.filter(
            publish_start__lte=timezone.now()
        ).filter(
            Q(publish_end__isnull=True) | Q(publish_end__gt=timezone.now())
        #).filter(
        #    site_wide=True
        )
        
        exclusions = request.session.get("excluded_announcements", set())
        if request.user.is_authenticated():
            for dismissal in request.user.announcement_dismissals.all():
                exclusions.add(dismissal.announcement.pk)
        else:
            qs = qs.exclude(members_only=True)
        context[self.as_var] = qs.exclude(pk__in=exclusions)
        return ""


@register.tag
def announcements(parser, token):
    """
    Usage::
        {% announcements as var %}
    
    Returns a list of announcements
    """
    return AnnouncementsNode.handle_token(parser, token)
