from django.shortcuts import redirect
from django.urls import reverse
from django.views import View

from user_messages.models import UserThread


class MarkReadUnread(View):

    def post(self, request, **kwargs):
        status_action = request.POST.get('action_type', '').lower()
        thread_ids = self._get_thread_ids(request.POST.keys())
        query_set = UserThread.objects.filter(user=request.user, thread__in=thread_ids)
        if status_action == 'read':
            query_set.update(unread=False)
        elif status_action == 'unread':
            query_set.update(unread=True)
        return redirect(reverse('messages_inbox'))

    def _get_thread_ids(self, post_keys):
        ids = []
        for key in post_keys:
            if 'thread' in key:
                ids.append(int(key.split('_')[1]))
        return ids
