from actstream.models import Action
from django.views.generic import ListView


class RecentActivity(ListView):
    """
    Returns recent public activity.
    """
    context_object_name = 'action_list'
    queryset = Action.objects.filter(public=True)[:15]
    template_name = 'social/activity_list.html'

    def get_context_data(self, *args, **kwargs):
        context = super(ListView, self).get_context_data(*args, **kwargs)
        context['action_list_layers'] = Action.objects.filter(
            public=True,
            action_object_content_type__name='layer')[:15]
        context['action_list_maps'] = Action.objects.filter(
            public=True,
            action_object_content_type__name='map')[:15]
        context['action_list_comments'] = Action.objects.filter(
            public=True,
            action_object_content_type__name='comment')[:15]
        return context
