import sys
import traceback
from pprint import pprint
from celery.task import task


from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import Group

from geonode.groups.models import GroupProfile, GroupMember

@task(name="geonode.tasks.requests.users", queue="users")

def join_user_to_groups(user, group_list):
    pprint(group_list)
    for g in group_list:
        group, created = Group.objects.get_or_create(name=str(g))
        group_profile = GroupProfile.objects.get_or_create(group=group)
        try:
            group_member = GroupMember.objects.get(group=group_profile.pk, user=user)
        except ObjectDoesNotExist as e:
            group_profile.join(user, role='member')
            
        user.groups.add(group)

