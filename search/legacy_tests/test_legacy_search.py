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

class SearchTests(SocialTestCase):

    def find(self, q):
        return self.client.get(reverse("search:search"), {"q": q}).content.decode()

    def test_a_person_is_found_by_their_last_name(self):
        """`last_name` was missing from the query, so searching for someone by
        the half of their name they were introduced by found nobody."""
        self.assertIn("asha", self.find("Kandel"))

    def test_a_person_is_found_by_their_first_name(self):
        self.assertIn("asha", self.find("Asha"))

    def test_a_person_is_found_by_their_username(self):
        self.assertIn("asha", self.find("ash"))

    def test_a_person_is_found_by_their_bio(self):
        self.assertIn("asha", self.find("Fridays"))

    def test_search_is_case_insensitive(self):
        self.assertIn("asha", self.find("KANDEL"))

    def test_a_person_is_listed_once_even_when_two_fields_match(self):
        """Two OR'd `icontains` across a joined table returns the same row
        twice without `.distinct()`. Counted inside the People section only —
        the right rail suggests the same person, and that is not a duplicate."""
        body = self.find("asha")
        section = body[body.index(">People<"):body.index(">Posts<")]
        profile_url = reverse("accounts:user-profile", args=["asha"])
        self.assertEqual(section.count(f'href="{profile_url}"'), 2)  # avatar + name

    def test_posts_are_found_too(self):
        Post.objects.create(author=self.other, text="a post about migrations")
        self.assertIn("a post about migrations", self.find("migrations"))

    def test_search_still_does_not_leak_a_private_post(self):
        Post.objects.create(author=self.other, text="secret migrations",
                            followers_only=True)
        self.assertNotIn("secret migrations", self.find("migrations"))

    def test_one_character_is_not_a_search(self):
        body = self.find("a")
        self.assertIn("No people matched", body)
