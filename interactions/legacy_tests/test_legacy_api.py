"""Tests migrated from palshare/test_social.py."""

"""The six things QA reported after the media upload landed.

Four of them were features that had never been built and two were defects in
features that had. They are tested together because they were reported
together, and because the pattern behind four of them is the same one: a
control that exists in the markup and nothing behind it. That pattern is what
this file is really guarding against.
"""

import shutil

import tempfile

from unittest.mock import patch

from django.contrib.auth import get_user_model

from django.core.exceptions import ValidationError

from django.core.files.uploadedfile import SimpleUploadedFile

from django.test import TestCase, override_settings

from django.urls import reverse

from rest_framework.test import APIClient

from accounts.models import Profile

from posts.models import Post

from connections.models import Follow

from interactions.models import Like, Reaction

from messaging.models import Conversation, Message

from accounts.services import set_avatar

from interactions.services import set_reaction
from messaging.services import edit_message, unsend_message

from io import BytesIO

from PIL import Image

User = get_user_model()

MEDIA_ROOT = tempfile.mkdtemp(prefix="palshare-social-media-")

def an_image(name="face.png"):
    # return SimpleUploadedFile(name, b"x" * 16, content_type="image/png")
    image = Image.new("RGB", (1, 1))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return SimpleUploadedFile(
        name,
        buffer.getvalue(),
        content_type="image/png",
    )

class SocialTestCase(TestCase):
    def setUp(self):
        self.me = User.objects.create_user(
            username="bello",
            email="bello@example.com",
            password="testpassword123",
            first_name="Bello",
        )

        self.other = User.objects.create_user(
            username="asha",
            email="asha@example.com",
            password="testpassword123",
            first_name="Asha",
        )

        # Profile is automatically created by accounts.signals
        self.me_profile = Profile.objects.get(user=self.me)
        self.other_profile = Profile.objects.get(user=self.other)

        self.other_profile.bio = "Ships things on Fridays"
        self.other_profile.save(update_fields=["bio"])

        self.client.force_login(self.me)

class ReactionApiTests(SocialTestCase):
    """`react` exists on the API for the same reason `like` does: the page and
    the API share `services.set_reaction`, so they cannot disagree about it."""

    def setUp(self):
        super().setUp()
        self.post = Post.objects.create(author=self.other, text="react to me")
        self.url = f"/api/palshare/posts/{self.post.pk}/react/"
        self.thumbs = Reaction.EMOJI[0][0]
        # DRF's SessionAuthentication enforces CSRF on unsafe methods, which
        # the plain test client does not carry. `force_authenticate` is how the
        # rest of `test_api.py` does it.
        self.client = APIClient()
        self.client.force_authenticate(self.me)

    def test_reacting_through_the_api_stores_the_same_row(self):
        response = self.client.post(self.url, {"emoji": self.thumbs},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["emoji"], self.thumbs)
        self.assertEqual(Reaction.objects.get().emoji, self.thumbs)

    def test_the_api_toggles_the_same_way_the_page_does(self):
        for _ in range(2):
            self.client.post(self.url, {"emoji": self.thumbs},
                            content_type="application/json")
        self.assertEqual(Reaction.objects.count(), 0)

    def test_an_emoji_outside_the_palette_is_a_400_not_a_500(self):
        response = self.client.post(self.url, {"emoji": "\U0001f4a3"},
                                    content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("emoji", response.json())

    def test_the_feed_serializer_reports_reactions(self):
        set_reaction(self.me, self.post, self.thumbs)
        row = self.client.get("/api/palshare/posts/").json()["results"][0]
        mine = [r for r in row["reactions"] if r["mine"]]
        self.assertEqual([r["emoji"] for r in mine], [self.thumbs])
        self.assertEqual(sum(r["count"] for r in row["reactions"]), 1)

class InteractionPermissionApiTests(SocialTestCase):
    """You could only like your own posts through the API.

    `IsAuthorOrReadOnly` was on the whole viewset, so every interaction on
    somebody else's post was a 403 — while the same interaction on the same
    post worked fine from the page, because the pages never used that
    permission class. Page and API disagreeing about a write is exactly what
    `services.py` was written to make impossible.
    """

    def setUp(self):
        super().setUp()
        self.theirs = Post.objects.create(author=self.other, text="not mine")
        self.client = APIClient()
        self.client.force_authenticate(self.me)

    def act(self, action, post=None):
        post = post or self.theirs
        return self.client.post(f"/api/palshare/posts/{post.pk}/{action}/",
                                {"emoji": Reaction.EMOJI[0][0]} if action == "react" else None,
                                format="json")

    def test_every_interaction_works_on_somebody_elses_post(self):
        for action in sorted(("like", "unlike", "save", "unsave",
                            "share", "unshare", "react")):
            with self.subTest(action=action):
                self.assertEqual(self.act(action).status_code, 200)

    def test_editing_somebody_elses_post_is_still_forbidden(self):
        # The permission was not removed, only narrowed to what it is about.
        response = self.client.patch(f"/api/palshare/posts/{self.theirs.pk}/",
                                    {"text": "rewritten by me"}, format="json")
        self.assertEqual(response.status_code, 403)
        self.theirs.refresh_from_db()
        self.assertEqual(self.theirs.text, "not mine")

    def test_deleting_somebody_elses_post_is_still_forbidden(self):
        response = self.client.delete(f"/api/palshare/posts/{self.theirs.pk}/")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Post.objects.filter(pk=self.theirs.pk).exists())

    def test_you_still_cannot_interact_with_a_post_you_cannot_see(self):
        hidden = Post.objects.create(author=self.other, text="followers only",
                                    followers_only=True)
        self.assertEqual(self.act("like", hidden).status_code, 404)
