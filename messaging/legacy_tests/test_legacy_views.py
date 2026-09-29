"""Tests migrated from palshare/test_views.py."""

"""The HTML half: does every page render, and does it obey the rules?

The contract these check is `demo.py` — the keys each template reads. A view is
correct when its context has the same shape the shell was built against, which
is why several of these assert on rendered markup rather than on a queryset.
"""

from django.contrib.auth import get_user_model

from django.db import connection

from django.test.utils import CaptureQueriesContext

from django.test import TestCase

from django.urls import reverse

from accounts.models import Profile, User

from posts.models import Comment, Post

from messaging.models import Conversation

from connections.models import Follow

from interactions.models import Like, Save

User = get_user_model()

PASSWORD = "lab-passphrase-2026"

class PalShareTestCase(TestCase):
    """Two accounts and a handful of rows — the same fixture every test wants."""

    def setUp(self):
        self.asha = User.objects.create_user("asha", password=PASSWORD, first_name="Asha")
        self.bello = User.objects.create_user("bello", password=PASSWORD, first_name="Bello")
        self.asha_profile = Profile.objects.get(user=self.asha)
        self.asha_profile.bio = "workshop"
        self.asha_profile.save(update_fields=["bio"])
        self.bello_profile = Profile.objects.get(user=self.bello)
        self.public = Post.objects.create(author=self.asha, text="a public post")
        self.private = Post.objects.create(author=self.asha, text="a followers-only post",
                                           followers_only=True)
        self.client.login(username="bello", password=PASSWORD)

class MessagingTests(PalShareTestCase):
    def setUp(self):
        super().setUp()
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.asha, self.bello)
        self.conversation.messages.create(sender=self.asha, text="are you there")

    def test_mine_comes_from_the_server(self):
        url = reverse("messaging:thread", args=[self.conversation.pk])
        sent = self.client.get(url).context["thread_messages"]
        self.assertEqual([m["mine"] for m in sent], [False])
        self.client.post(url, {"text": "I am"})
        self.assertEqual([m["mine"] for m in self.client.get(url).context["thread_messages"]],
                         [False, True])

    def test_the_thread_list_is_not_called_messages(self):
        """`messages` belongs to django.contrib.messages; a thread under that
        name renders itself as flash messages in base.html."""
        response = self.client.get(reverse("messaging:thread", args=[self.conversation.pk]))
        self.assertIn("thread_messages", response.context)

    def test_a_conversation_you_are_not_in_does_not_exist(self):
        theirs = Conversation.objects.create()
        theirs.participants.add(self.asha)
        response = self.client.get(reverse("messaging:thread", args=[theirs.pk]))
        self.assertEqual(response.status_code, 404)

    def test_opening_a_thread_clears_the_unread_badge(self):
        inbox = self.client.get(reverse("messaging:inbox")).context["conversations"]
        self.assertEqual(inbox[0]["unread"], 1)
        self.client.get(reverse("messaging:thread", args=[self.conversation.pk]))
        inbox = self.client.get(reverse("messaging:inbox")).context["conversations"]
        self.assertEqual(inbox[0]["unread"], 0)
