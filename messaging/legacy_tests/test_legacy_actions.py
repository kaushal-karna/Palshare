"""Tests migrated from palshare/test_interactions.py."""

"""The seven controls that used to render and do nothing.

Each one is a form now, so each one is testable the way a form is: post to it
and look at the row it was supposed to create. The pair of tests that matters
most in here is the toggle pair — press once, press again, and end up where
you started, with the counter cache still telling the truth.
"""

from django.contrib.auth import get_user_model

from django.test import TestCase

from django.urls import reverse

from accounts.models import Profile

from posts.models import Comment, Post

from interactions.models import CommentLike, Like, Share, Save

from connections.models import Follow

from messaging.models import Conversation

from interactions.services import set_like

User = get_user_model()

PASSWORD = "lab-passphrase-2026"

class InteractionTestCase(TestCase):
    def setUp(self):
        self.asha = User.objects.create_user("asha", password=PASSWORD, first_name="Asha")
        self.bello = User.objects.create_user("bello", password=PASSWORD, first_name="Bello")
        self.asha_profile = Profile.objects.get(user=self.asha)
        self.bello_profile = Profile.objects.get(user=self.bello)
        self.post = Post.objects.create(author=self.asha, text="press things on me")
        self.comment = Comment.objects.create(post=self.post, author=self.asha, text="a comment")
        self.client.login(username="bello", password=PASSWORD)
        self.feed = reverse("posts:feed")

    def press(self, name, args, **data):
        return self.client.post(reverse(name, args=args), {"next": self.feed, **data})

class MessageActionTests(InteractionTestCase):
    def test_messaging_someone_opens_one_conversation_and_keeps_it(self):
        response = self.press("messaging:message-user", ["asha"])
        conversation = Conversation.objects.get()
        self.assertRedirects(response, reverse("messaging:thread", args=[conversation.pk]))

        self.press("messaging:message-user", ["asha"])
        self.assertEqual(Conversation.objects.count(), 1)

    def test_it_is_the_same_conversation_from_either_side(self):
        self.press("messaging:message-user", ["asha"])
        self.client.login(username="asha", password=PASSWORD)
        self.press("messaging:message-user", ["bello"])
        self.assertEqual(Conversation.objects.count(), 1)

    def test_you_cannot_message_yourself(self):
        response = self.press("messaging:message-user", ["bello"])
        self.assertRedirects(response, reverse("messaging:inbox"))
        self.assertEqual(Conversation.objects.count(), 0)
