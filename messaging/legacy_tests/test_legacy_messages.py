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

class MessageEditTests(SocialTestCase):
    def setUp(self):
        super().setUp()
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.me, self.other)
        self.mine = Message.objects.create(conversation=self.conversation,
                                           sender=self.me, text="ment to say this")
        self.theirs = Message.objects.create(conversation=self.conversation,
                                             sender=self.other, text="their words")

    def edit(self, message, text):
        return self.client.post(reverse("messaging:message-edit", args=[message.pk]),
                                {"text": text})

    def unsend(self, message):
        return self.client.post(reverse("messaging:message-unsend", args=[message.pk]))

    def test_editing_changes_the_text_and_stamps_it(self):
        self.edit(self.mine, "meant to say this")
        self.mine.refresh_from_db()
        self.assertEqual(self.mine.text, "meant to say this")
        self.assertIsNotNone(self.mine.edited_at)

    def test_an_edited_message_says_so_in_the_thread(self):
        self.edit(self.mine, "fixed")
        body = self.client.get(reverse("messaging:thread",
                                    args=[self.conversation.pk])).content.decode()
        self.assertIn("· edited", body)

    def test_you_cannot_edit_somebody_elses_message(self):
        self.edit(self.theirs, "words I put in their mouth")
        self.theirs.refresh_from_db()
        self.assertEqual(self.theirs.text, "their words")

    def test_unsending_removes_the_text_from_the_database(self):
        self.unsend(self.mine)
        self.mine.refresh_from_db()
        # Not hidden in the template — gone. A message the server still stores
        # is not unsent.
        self.assertEqual(self.mine.text, "")
        self.assertTrue(self.mine.is_deleted)

    def test_an_unsent_message_keeps_its_place_in_the_thread(self):
        self.unsend(self.mine)
        body = self.client.get(reverse("messaging:thread",
                                    args=[self.conversation.pk])).content.decode()
        self.assertIn("This message was unsent.", body)
        self.assertNotIn("ment to say this", body)

    def test_you_cannot_unsend_somebody_elses_message(self):
        self.unsend(self.theirs)
        self.theirs.refresh_from_db()
        self.assertEqual(self.theirs.text, "their words")

    def test_unsending_twice_is_not_an_error(self):
        self.unsend(self.mine)
        response = self.unsend(self.mine)
        self.assertEqual(response.status_code, 302)

    def test_an_unsent_message_cannot_be_edited_back_into_existence(self):
        unsend_message(self.me, self.mine)
        with self.assertRaises(ValidationError):
            edit_message(self.me, self.mine, "back from the dead")

    def test_an_edit_cannot_be_used_to_empty_a_message(self):
        with self.assertRaises(ValidationError):
            edit_message(self.me, self.mine, "   ")

    def test_a_stranger_cannot_reach_a_message_at_all(self):
        stranger = User.objects.create_user("nosy", password="pw")
        self.client.force_login(stranger)
        response = self.unsend(self.mine)
        self.assertEqual(response.status_code, 404)

    def test_the_edit_form_opens_on_your_own_bubble_only(self):
        url = reverse("messaging:thread", args=[self.conversation.pk])
        body = self.client.get(url, {"edit": self.mine.pk}).content.decode()
        self.assertIn(f'action="{reverse("messaging:message-edit", args=[self.mine.pk])}"', body)

        body = self.client.get(url, {"edit": self.theirs.pk}).content.decode()
        self.assertNotIn("bubble-edit", body)

    def test_editing_refuses_a_get(self):
        response = self.client.get(reverse("messaging:message-edit", args=[self.mine.pk]))
        self.assertEqual(response.status_code, 405)
