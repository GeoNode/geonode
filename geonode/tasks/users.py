import sys
import traceback
from pprint import pprint
from celery.task import task


from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import Group

from geonode.groups.models import GroupProfile, GroupMember

@task(name="geonode.tasks.requests.users", queue="users")

def join_user_to_groups(user, group_list):
    for g in group_list:
        group, created = GroupProfile.objects.get_or_create(
            title=str(g)
        )

        try:
            group_member = GroupMember.objects.get(group=group, user=user)
        except ObjectDoesNotExist as e:
            group.join(user, role='member')

