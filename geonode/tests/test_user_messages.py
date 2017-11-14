from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase

from user_messages.models import Message


class UserMessagesTestCase(TestCase):

    def setUp(self):
        self.user_password = "somepass"
        self.first_user = get_user_model().objects.create_user(
            "someuser", "someuser@fakemail.com", self.user_password)
        self.second_user = get_user_model().objects.create_user(
            "otheruser", "otheruser@fakemail.com", self.user_password)
        first_message = Message.objects.new_message(
            from_user=self.first_user,
            subject="testing message",
            content="some content",
            to_users=[self.second_user]
        )
        self.thread = first_message.thread

    def test_inbox_renders(self):
        self.client.login(
            username=self.first_user.username, password=self.user_password)
        response = self.client.get(reverse("messages_inbox"))
        self.assertTemplateUsed(response, "user_messages/inbox.html")
        self.assertEqual(response.status_code, 200)

    def test_inbox_redirects_when_not_logged_in(self):
        target_url = reverse("messages_inbox")
        response = self.client.get(target_url)
        self.assertRedirects(
            response,
            "{}?next={}".format(reverse("account_login"), target_url)
        )

    def test_new_message_renders(self):
        self.client.login(
            username=self.first_user.username, password=self.user_password)
        response = self.client.get(
            reverse("message_create", args=(self.first_user.id,)))
        self.assertTemplateUsed(response, "user_messages/message_create.html")
        self.assertEqual(response.status_code, 200)

    def test_new_message_redirects_when_not_logged_in(self):
        target_url = reverse("message_create", args=(self.first_user.id,))
        response = self.client.get(target_url)
        self.assertRedirects(
            response,
            "{}?next={}".format(reverse("account_login"), target_url)
        )

    def test_thread_detail_renders(self):
        self.client.login(
            username=self.first_user.username, password=self.user_password)
        response = self.client.get(
            reverse("messages_thread_detail", args=(self.thread.id,)))
        self.assertTemplateUsed(response, "user_messages/thread_detail.html")
        self.assertEqual(response.status_code, 200)

    def test_thread_detail_redirects_when_not_logged_in(self):
        target_url = reverse("messages_thread_detail", args=(self.thread.id,))
        response = self.client.get(target_url)
        self.assertRedirects(
            response,
            "{}?next={}".format(reverse("account_login"), target_url)
        )
