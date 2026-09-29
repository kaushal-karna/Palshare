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

class PagerTests(InteractionTestCase):
    def test_paging_keeps_the_rest_of_the_query_string(self):
        """A bare `?page=2` silently drops the tab you were on."""
        Follow.objects.create(follower=self.bello, following=self.asha)
        for i in range(25):
            Post.objects.create(author=self.asha, text=f"post {i}")
        body = self.client.get(self.feed, {"filter": "following"}).content.decode()
        self.assertIn("filter=following&amp;page=2", body)

    def test_the_following_tab_means_people_you_follow(self):
        mine = Post.objects.create(author=self.bello, text="my own post")
        body = self.client.get(self.feed, {"filter": "following"}).content.decode()
        self.assertNotIn("my own post", body)
        self.assertNotIn("press things on me", body)  # asha, not followed yet

        Follow.objects.create(follower=self.bello, following=self.asha)
        body = self.client.get(self.feed, {"filter": "following"}).content.decode()
        self.assertIn("press things on me", body)
        self.assertNotIn(mine.text, body)
