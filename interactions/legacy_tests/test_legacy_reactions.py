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

class ReactionTests(SocialTestCase):
    def setUp(self):
        super().setUp()
        self.post = Post.objects.create(author=self.other, text="react to me")
        self.thumbs, self.heart = Reaction.EMOJI[0][0], Reaction.EMOJI[1][0]

    def react(self, emoji):
        return self.client.post(reverse("interactions:post-react", args=[self.post.pk]),
                                {"emoji": emoji})

    def test_reacting_stores_the_emoji(self):
        self.react(self.thumbs)
        self.assertEqual(Reaction.objects.get(user=self.me, post=self.post).emoji,
                         self.thumbs)

    def test_pressing_the_same_one_again_takes_it_back(self):
        self.react(self.thumbs)
        self.react(self.thumbs)
        self.assertEqual(Reaction.objects.count(), 0)

    def test_a_different_emoji_replaces_rather_than_adds(self):
        self.react(self.thumbs)
        self.react(self.heart)
        self.assertEqual(Reaction.objects.count(), 1)
        self.assertEqual(Reaction.objects.get().emoji, self.heart)

    def test_two_people_can_react_to_the_same_post(self):
        self.react(self.thumbs)
        self.client.force_login(self.other)
        self.react(self.thumbs)
        self.assertEqual(Reaction.objects.filter(post=self.post).count(), 2)

    def test_an_emoji_outside_the_palette_is_refused(self):
        with self.assertRaises(ValidationError):
            set_reaction(self.me, self.post, "\U0001f4a3")
        self.assertEqual(Reaction.objects.count(), 0)

    def test_the_endpoint_refuses_it_too_not_just_the_service(self):
        # The palette is enforced by the server, not by the five buttons the
        # template happens to render.
        self.react("\U0001f4a3")
        self.assertEqual(Reaction.objects.count(), 0)

    def test_the_bar_shows_the_whole_palette_with_counts(self):
        self.react(self.thumbs)
        body = self.client.get(reverse("posts:feed")).content.decode()
        self.assertEqual(body.count('class="reaction '), len(Reaction.EMOJI))
        self.assertIn("reaction-on", body)

    def test_reacting_refuses_a_get(self):
        response = self.client.get(reverse("interactions:post-react", args=[self.post.pk]))
        self.assertEqual(response.status_code, 405)

    def test_you_cannot_react_to_a_post_you_cannot_see(self):
        hidden = Post.objects.create(author=self.other, text="followers only",
                                     followers_only=True)
        response = self.client.post(reverse("interactions:post-react", args=[hidden.pk]),
                                    {"emoji": self.thumbs})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Reaction.objects.count(), 0)

    def test_the_picker_is_offered_on_every_box_you_can_type_in(self):
        conversation = Conversation.objects.create()
        conversation.participants.add(self.me, self.other)
        pages = [
            (reverse("posts:feed"), "composer-text"),
            (reverse("posts:post-detail", args=[self.post.pk]), "comment-text"),
            (reverse("messaging:thread", args=[conversation.pk]), "message-text"),
            (reverse("posts:post-create"), "id_text"),
        ]
        for url, target in pages:
            body = self.client.get(url).content.decode()
            self.assertIn(f'data-emoji-picker="{target}"', body, msg=url)

    def test_typed_emoji_survive_a_round_trip(self):
        self.client.post(reverse("posts:feed"), {"text": "shipped it \U0001f680"})
        body = self.client.get(reverse("posts:feed")).content.decode()
        self.assertIn("\U0001f680", body)
