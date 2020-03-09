from django import template
from uuid import uuid4

register = template.Library()


@register.simple_tag
def is_unread(thread, user):
    if thread.userthread_set.filter(user=user, unread=True).count() > 0:
        return True
    return False


@register.simple_tag
def random_uuid():
    return str(uuid4())
