from django import template
from uuid import uuid4
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _

from user_messages.models import Message

register = template.Library()


@register.simple_tag
def is_unread(thread, user):
    if thread.userthread_set.filter(user=user, unread=True).count() > 0:
        return True
    return False


@register.simple_tag
def random_uuid():
    return str(uuid4())


@register.simple_tag
def format_senders(thread, current_user):
    User = get_user_model()
    users = User.objects.filter(sent_messages__thread=thread).order_by('sent_messages__sent_at').distinct()
    sender_string = ''
    u_count = users.count()
    if u_count < 3:
        for user in users:
            if user == current_user:
                user_repr = _('me')
            else:
                user_repr = f'{user.full_name_or_nick}'
            sender_string += f'{user_repr}, '
        sender_string = sender_string[:-2]
    elif u_count == 3:
        for user in users:
            if user == current_user:
                user_repr = _('me')
            else:
                user_repr = f'{user.first_name_or_nick}'
            sender_string += f'{user_repr}, '
        sender_string = sender_string[:-2]
    else:
        first_sender = thread.latest_message
        last_sender = thread.latest_message
        sender_string = f'{first_sender.first_name_or_nick} .. {last_sender.first_name_or_nick}'
    return f'{sender_string}'
