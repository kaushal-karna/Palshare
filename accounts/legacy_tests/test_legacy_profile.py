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

class ProfileAccessTests(SocialTestCase):

    def test_another_persons_profile_opens(self):
        response = self.client.get(reverse("accounts:user-profile", args=["asha"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Asha")

    def test_a_profile_opens_for_a_user_who_has_no_profile_row(self):
        # Anyone created by `createsuperuser`, the admin or a fixture — which
        # in a workshop database is most people.
        User.objects.create_user("kaushal", password="pw")
        response = self.client.get(reverse("accounts:user-profile", args=["kaushal"]))
        self.assertEqual(response.status_code, 200)

    def test_the_media_tab_shows_only_posts_with_files(self):
        Post.objects.create(author=self.other, text="just words")
        with_media = Post.objects.create(author=self.other, text="with a picture")
        with_media.media.create(file="posts/x.png", kind="image")

        body = self.client.get(reverse("accounts:user-profile", args=["asha"]),
                               {"tab": "media"}).content.decode()

        self.assertIn("with a picture", body)
        self.assertNotIn("just words", body)

    def test_the_media_tab_shows_a_post_once_per_post_not_once_per_file(self):
        post = Post.objects.create(author=self.other, text="three files")
        for i in range(3):
            post.media.create(file=f"posts/{i}.png", kind="image")

        body = self.client.get(reverse("accounts:user-profile", args=["asha"]),
                               {"tab": "media"}).content.decode()

        self.assertEqual(body.count("three files"), 1)

    def test_the_likes_tab_shows_what_they_liked(self):
        mine = Post.objects.create(author=self.me, text="they liked this")
        Like.objects.create(user=self.other, post=mine)
        Post.objects.create(author=self.other, text="their own post")

        body = self.client.get(reverse("accounts:user-profile", args=["asha"]),
                               {"tab": "likes"}).content.decode()

        self.assertIn("they liked this", body)
        self.assertNotIn("their own post", body)

    def test_an_invented_tab_falls_back_to_posts(self):
        response = self.client.get(reverse("accounts:user-profile", args=["asha"]),
                                   {"tab": "../../etc/passwd"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["tab"], "posts")

    def test_a_private_account_still_hides_its_posts_on_every_tab(self):
        self.other.is_private = True
        self.other.save()
        Post.objects.create(author=self.other, text="secret")

        for tab in ("posts", "media", "likes"):
            body = self.client.get(reverse("accounts:user-profile", args=["asha"]),
                                   {"tab": tab}).content.decode()
            self.assertNotIn("secret", body)
            self.assertIn("This account is private", body)

@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class AvatarTests(SocialTestCase):

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def edit_profile(self, **extra):
        return self.client.post(reverse("accounts:profile-edit", args=["bello"]),
                                {"name": "Bello", "bio": "", **extra})

    def test_uploading_a_picture_stores_it(self):
        """The view read `request.POST` and never `request.FILES`, so this
        input was discarded on every save without a word."""
        self.edit_profile(avatar=an_image())
        self.assertTrue(Profile.objects.get(user=self.me).avatar)

    def test_the_picture_is_rendered_instead_of_the_initial(self):
        self.edit_profile(avatar=an_image())
        body = self.client.get(reverse("accounts:user-profile", args=["bello"])).content.decode()
        self.assertIn("avatars/", body)
        self.assertIn('class="avatar-img"', body)

    def test_your_own_picture_shows_in_the_header_and_the_composer(self):
        """`shell()` hand-built `current_user` with three of the four keys the
        avatar partial reads, so your own picture was the one avatar on the
        page that stayed an initial."""
        self.edit_profile(avatar=an_image())
        body = self.client.get(reverse("posts:feed")).content.decode()
        header = body[:body.index('class="shell"')]
        self.assertIn("avatar-img", header)
        composer = body[body.index('class="composer"'):body.index("composer-body")]
        self.assertIn("avatar-img", composer)

    def test_it_shows_up_on_other_peoples_screens_too(self):
        self.edit_profile(avatar=an_image())
        self.client.force_login(self.other)
        body = self.client.get(reverse("accounts:user-profile", args=["bello"])).content.decode()
        self.assertIn("avatars/", body)

    def test_saving_without_a_new_picture_keeps_the_old_one(self):
        self.edit_profile(avatar=an_image())
        self.edit_profile(bio="changed my mind about the bio")
        self.assertTrue(Profile.objects.get(user=self.me).avatar)

    def test_someone_with_no_picture_still_gets_their_initial(self):
        body = self.client.get(reverse("accounts:user-profile", args=["asha"])).content.decode()
        self.assertNotIn('class="avatar-img"', body)
        self.assertIn(">\n\n  A\n\n<", body)

    def test_a_video_is_not_a_profile_picture(self):
        with self.assertRaises(ValidationError):
            set_avatar(self.me.profile, SimpleUploadedFile("me.mp4", b"x" * 8))

    def test_a_rejected_picture_says_why_and_changes_nothing(self):
        response = self.edit_profile(avatar=SimpleUploadedFile("resume.pdf", b"x" * 8))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Profile.objects.get(user=self.me).avatar)
        self.assertContains(response, "resume.pdf")

    def test_you_cannot_edit_somebody_elses_profile(self):
        response = self.client.post(reverse("accounts:profile-edit", args=["asha"]),
                                        {"name": "Not Asha"})
        self.assertEqual(response.status_code, 403)

    def test_a_user_with_no_profile_row_does_not_break_a_byline(self):
        stray = User.objects.create_user("kaushal", password="pw")
        Post.objects.create(author=stray, text="from someone with no profile row")
        response = self.client.get(reverse("posts:feed"))
        self.assertEqual(response.status_code, 200)
