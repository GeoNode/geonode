from guardian.models import UserObjectPermission, GroupObjectPermission
from guardian.shortcuts import get_perms
from guardian.compat import get_user_model
from django.contrib.contenttypes.models import ContentType
import bisect
from django.db.models.query_utils import Q


def get_users_with_perms(obj, attach_perms=True, with_superusers=True,
        with_group_users=True):
    all_user_perms = dict()
    
    #Retrieve superusers
    if with_superusers:
        superusers=get_user_model().objects.filter(Q(is_superuser=True))
        for s_user in superusers:
            all_user_perms[s_user] = sorted(get_perms(s_user, obj))
    
    #Retrieve users with direct permissions 
    obj_content_type = ContentType.objects.get_for_model(obj)
    user_perms = UserObjectPermission.objects.filter(content_type=obj_content_type,object_pk=obj.id)
    for p in user_perms:
        if p.user in all_user_perms:
            bisect.insort_left(all_user_perms[p.user],p.permission.codename)
        else:
            all_user_perms[p.user] = [p.permission.codename]
    #Retrieve users with permissions via group
    if with_group_users:
        group_perms = get_groups_with_perms(obj,)        
        for g, perms in group_perms.iteritems():   #Iterate over each group
            if g.name == "anonymous":
                for g_user in g.user_set.all(): #Iterate over each user in each group
                    if g_user in all_user_perms:
                        current_perms = list(all_user_perms[g_user])
                        current_perms.extend(p for p in perms if p not in current_perms)
                        all_user_perms[g_user] = sorted(current_perms)
                    else:
                        all_user_perms[g_user] = sorted(perms)
            else:
                for g_mem in g.groupprofile.member_queryset():   # Iterate over group members using group profile
                    user=g_mem.user
                    if user in all_user_perms:   # Add unique permissions not found in current perms of user
                        current_perms = list(all_user_perms[user])
                        current_perms.extend(p for p in perms if p not in current_perms)
                        all_user_perms[user] = sorted(current_perms)
                    else:
                        all_user_perms[user] = sorted(perms)
    return all_user_perms

def get_groups_with_perms(obj, attach_perms=True):
    
    all_group_perms = dict()
    
    obj_content_type = ContentType.objects.get_for_model(obj)
    group_perms = GroupObjectPermission.objects.filter(content_type=obj_content_type,object_pk=obj.id)
    for p in group_perms:
        if p.group in all_group_perms:
            bisect.insort_left(all_group_perms[p.group],p.permission.codename)
        else:
            all_group_perms[p.group] = [p.permission.codename]
    
    return all_group_perms
