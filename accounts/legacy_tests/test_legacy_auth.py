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

class AuthTests(TestCase):
    def test_registering_creates_a_profile_and_signs_you_in(self):
        response = self.client.post(reverse("accounts:register"),
                                    {"username": "kaushal", "email": "k@lab.test",
                                     "password": PASSWORD})
        self.assertRedirects(response, reverse("posts:feed"))
        self.assertTrue(Profile.objects.filter(user__username="kaushal").exists())

    def test_a_taken_username_says_so(self):
        User.objects.create_user("kaushal", password=PASSWORD)
        response = self.client.post(reverse("accounts:register"),
                                    {"username": "kaushal", "password": PASSWORD})
        self.assertContains(response, "That username is taken")

    def test_a_bad_password_renders_the_login_error(self):
        User.objects.create_user("kaushal", password=PASSWORD)
        response = self.client.post(reverse("accounts:login"),
                                    {"username": "kaushal", "password": "wrong"})
        self.assertContains(response, "did not match")

    def test_logout_is_a_post(self):
        user = User.objects.create_user(
            username="kaushal",
            email="k@lab.test",
            password=PASSWORD,
        )
        #The signal automatically creates the profile.
        self.client.force_login(user)
        # A GET logout can be triggered by any <img> tag on the internet.
        self.assertEqual(self.client.get(reverse("accounts:settings")).status_code, 200)
        response = self.client.post(reverse("accounts:settings"), {"logout": "1"})
        self.assertRedirects(response, reverse("accounts:login"))
