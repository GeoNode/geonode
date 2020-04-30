from django.shortcuts import redirect
from django.urls import reverse
from django.views import View

from user_messages.models import UserThread, GroupMemberThread


class MarkReadUnread(View):

    def post(self, request, **kwargs):
        status_action = request.POST.get('action_type', '').lower()
        thread_ids = self._get_thread_ids()
        user_threads = UserThread.objects.filter(user=request.user, thread__in=thread_ids)
        group_member_threads = GroupMemberThread.objects.filter(user=request.user, thread__in=thread_ids)
        if status_action == 'read':
            group_member_threads.update(unread=False)
            user_threads.update(unread=False)
        elif status_action == 'unread':
            group_member_threads.update(unread=True)
            user_threads.update(unread=True)
        return redirect(reverse('messages_inbox'))

    def _get_thread_ids(self):
        ids = []
        for key in self.request.POST.keys():
            if 'thread' in key and self.request.POST.get(key).lower() == 'true':
                ids.append(int(key.split('_')[1]))
        return ids
