from django import template


register = template.Library()

@register.filter
def unread(thread, user):
    return bool(thread.userthread_set.filter(user=user, unread=True))

