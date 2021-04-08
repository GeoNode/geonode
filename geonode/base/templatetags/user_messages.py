# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
from uuid import uuid4
from django import template
from django.conf import settings
from django.db.models import Sum
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _

register = template.Library()


@register.simple_tag
def is_unread(thread, user):
    if thread.userthread_set.filter(user=user, unread=True).count() > 0 or \
            thread.groupmemberthread_set.filter(user=user, unread=True).count() > 0:
        return True
    return False


@register.simple_tag
def random_uuid():
    return str(uuid4())


@register.simple_tag
def format_senders(thread, current_user):
    User = get_user_model()
    users = User.objects.filter(sent_messages__thread=thread).annotate(Sum('pk'))
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
        first_sender = thread.first_message.sender
        last_sender = thread.latest_message.sender
        sender_string = f'{first_sender.first_name_or_nick} .. {last_sender.first_name_or_nick}'
    return f'{sender_string}'


@register.simple_tag
def get_item(dictionary, key):
    return dictionary.get(key, [])


@register.simple_tag
def show_notification(notice_type_label, current_user):
    adms_notice_types = getattr(settings, 'ADMINS_ONLY_NOTICE_TYPES', [])
    if not current_user.is_superuser and adms_notice_types and \
            notice_type_label in adms_notice_types:
        return False
    return True
