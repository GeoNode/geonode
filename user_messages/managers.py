from django.db.models import Manager

from user_messages.signals import message_sent


class ThreadManager(Manager):
    
    def inbox(self, user):
        return self.filter(userthread__user=user, userthread__deleted=False)

    def all(self, user):
        return self.filter(userthread__user=user)

    def unread(self, user):
        return self.filter(userthread__user=user, userthread__deleted=False, userthread__unread=True)

    def search_message(self, user, search_text):
        return self.filter(
            userthread__user=user,
            messages__content__contains=search_text,
            subject__contains=search_text)


class MessageManager(Manager):
    
    def new_reply(self, thread, user, content):
        msg = self.create(thread=thread, sender=user, content=content)
        thread.userthread_set.exclude(user=user).update(deleted=False, unread=True)
        message_sent.send(sender=self.model, message=msg, thread=thread, reply=True)
        return msg
    
    def new_message(self, from_user, to_users, subject, content):
        from user_messages.models import Thread
        thread = Thread.objects.create(subject=subject)
        for user in to_users:
            if user != from_user:
                thread.userthread_set.create(user=user, deleted=False, unread=True)
        if from_user in to_users:
            thread.userthread_set.create(user=from_user, deleted=False, unread=True)
        else:
            thread.userthread_set.create(user=from_user, deleted=True, unread=False)
        msg = self.create(thread=thread, sender=from_user, content=content)
        message_sent.send(sender=self.model, message=msg, thread=thread, reply=False)
        return msg
