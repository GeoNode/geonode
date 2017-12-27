import os

from django.conf import settings
from django.core.urlresolvers import reverse
from django.template import Context

from django.contrib.auth.models import User

from eldarion.test import TestCase

from user_messages.models import Thread, Message


class BaseTest(TestCase):
    def setUp(self):
        self.brosner = User.objects.create_superuser("brosner",
            "brosner@brosner.brosner", "abc123")
        self.jtauber = User.objects.create_superuser("jtauber",
            "jtauber@jtauber.jtauber", "abc123")
        if hasattr(self, "template_dirs"):
            self._old_template_dirs = settings.TEMPLATE_DIRS
            settings.TEMPLATE_DIRS = self.template_dirs
    
    def tearDown(self):
        if hasattr(self, "_old_template_dirs"):
            settings.TEMPLATE_DIRS = self._old_template_dirs


class TestMessages(BaseTest):
    def test_messages(self):
        Message.objects.new_message(self.brosner, [self.jtauber], "Really?",
            "You can't be serious")
        
        self.assertEqual(Thread.objects.inbox(self.brosner).count(), 0)
        self.assertEqual(Thread.objects.inbox(self.jtauber).count(), 1)
        
        thread = Thread.objects.inbox(self.jtauber)[0]
        
        Message.objects.new_reply(thread, self.jtauber, "Yes, I am.")
        
        self.assertEqual(Thread.objects.inbox(self.brosner).count(), 1)
        self.assertEqual(Thread.objects.inbox(self.jtauber).count(), 1)
        
        Message.objects.new_reply(thread, self.brosner, "If you say so...")
        Message.objects.new_reply(thread, self.jtauber, "Indeed I do")
        
        self.assertEqual(Thread.objects.get(pk=thread.pk).latest_message.content,
            "Indeed I do")
        self.assertEqual(Thread.objects.get(pk=thread.pk).first_message.content,
            "You can't be serious")
    
    def test_ordered(self):
        t1 = Message.objects.new_message(self.brosner, [self.jtauber], "Subject",
            "A test message").thread
        t2 = Message.objects.new_message(self.brosner, [self.jtauber], "Another",
            "Another message").thread
        t3 = Message.objects.new_message(self.brosner, [self.jtauber], "Pwnt",
            "Haha I'm spamming your inbox").thread
        self.assertEqual(Thread.ordered([t2, t1, t3]), [t3, t2, t1])


class TestMessageViews(BaseTest):
    template_dirs = [
        os.path.join(os.path.dirname(__file__), "templates")
    ]

    def test_create_message(self):
        with self.login("brosner", "abc123"):
            response = self.get("messages_inbox")
            self.assertEqual(response.status_code, 200)
            
            response = self.get("message_create")
            self.assertEqual(response.status_code, 200)
            
            data = {
                "subject": "The internet is down.",
                "content": "Does this affect any of our sites?",
                "to_user": str(self.jtauber.id)
            }
            
            response = self.post("message_create", data=data)
            self.assertEqual(response.status_code, 302)
            
            self.assertEqual(Thread.objects.inbox(self.jtauber).count(), 1)
            self.assertEqual(Thread.objects.inbox(self.brosner).count(), 0)
            
            response = self.get("message_create", user_id=self.jtauber.id)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "selected=\"selected\">jtauber</option>")
            
            thread_id = Thread.objects.inbox(self.jtauber).get().id
            
            response = self.get("messages_thread_detail", thread_id=thread_id)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Does this affect any of our sites?")
            
        with self.login("jtauber", "abc123"):
            response = self.get("messages_inbox")
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Does this affect")
            
            response = self.get("messages_thread_detail", thread_id=thread_id)
            self.assertContains(response, "Does this affect")
            
            response = self.post("messages_thread_delete", thread_id=thread_id)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(Thread.objects.inbox(self.jtauber).count(), 0)
            
            data = {
                "content": "Nope, the internet being down doesn't affect us.",
            }
            
            response = self.post("messages_thread_detail", thread_id=thread_id, data=data)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(Thread.objects.inbox(self.brosner).count(), 1)
            self.assertEqual(
                Thread.objects.inbox(self.brosner).get().messages.count(),
                2
            )
            self.assertEqual(Thread.objects.unread(self.jtauber).count(), 0)
    
    def test_urls(self):
        self.assertEqual(reverse("message_create", args=[10]), "/create/10/")

class TestTemplateTags(BaseTest):
    def test_unread(self):
        thread = Message.objects.new_message(self.brosner, [self.jtauber], "Why did you the internet?", "I demand to know.").thread
        tmpl = """{% load user_messages_tags %}{% if thread|unread:user %}UNREAD{% else %}READ{% endif %}"""
        self.assert_renders(
            tmpl,
            Context({"thread": thread, "user": self.jtauber}),
            "UNREAD"
        )
        self.assert_renders(
            tmpl,
            Context({"thread": thread, "user": self.brosner}),
            "READ",
        )
