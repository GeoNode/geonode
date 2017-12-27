from datetime import datetime

from django.core.urlresolvers import reverse
from django.db import models

from django.conf import settings
from django.utils import timezone

from user_messages.managers import ThreadManager, MessageManager
from user_messages.utils import cached_attribute


class Thread(models.Model):
    
    subject = models.CharField(max_length=150)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through="UserThread")
    
    objects = ThreadManager()
    
    def get_absolute_url(self):
        return reverse("messages_thread_detail", kwargs={"thread_id": self.pk})
    
    @property
    @cached_attribute
    def first_message(self):
        return self.messages.all()[0]
    
    @property
    @cached_attribute
    def latest_message(self):
        return self.messages.order_by("-sent_at")[0]
    
    @classmethod
    def ordered(cls, objs):
        """
        Returns the iterable ordered the correct way, this is a class method 
        because we don"t know what the type of the iterable will be.
        """
        objs = list(objs)
        objs.sort(key=lambda o: o.latest_message.sent_at, reverse=True)
        return objs


class UserThread(models.Model):
    
    thread = models.ForeignKey(Thread)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    
    unread = models.BooleanField()
    deleted = models.BooleanField()


class Message(models.Model):
    
    thread = models.ForeignKey(Thread, related_name="messages")
    
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="sent_messages")
    sent_at = models.DateTimeField(default=timezone.now)
    
    content = models.TextField()
    
    objects = MessageManager()
    
    class Meta:
        ordering = ("sender",)
    
    def get_absolute_url(self):
        return self.thread.get_absolute_url()
