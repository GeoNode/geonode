from actstream.models import Action
from django.views.generic import ListView


class RecentActivity(ListView):
    """
    Returns recent public activity.
    """
    context_object_name = 'action_list'
    queryset = Action.objects.filter(public=True)[:15]
    template_name = 'social/activity_list.html'
