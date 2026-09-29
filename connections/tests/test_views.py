from django.contrib.auth import get_user_model

from django.test import TestCase
from django.urls import reverse

from connections.models import Follow


User = get_user_model()

PASSWORD = "lab-passphrase-2026"


class ConnectionActionTestCase(TestCase):
    def setUp(self):
        self.asha = User.objects.create_user(
            "asha",
            password=PASSWORD,
            first_name="Asha",
        )
        self.bello = User.objects.create_user(
            "bello",
            password=PASSWORD,
            first_name="Bello",
        )

        self.other = self.asha

        self.client.login(
            username="bello",
            password=PASSWORD,
        )
        self.feed = reverse("posts:feed")

    def press(self, name, args, **data):
        return self.client.post(
            reverse(name, args=args),
            {"next": self.feed, **data},
        )


class FollowActionTests(ConnectionActionTestCase):
    def test_follow_toggles(self):
        self.press("connections:user-follow", ["asha"])
        self.assertEqual(Follow.objects.count(), 1)
        self.press("connections:user-follow", ["asha"])
        self.assertEqual(Follow.objects.count(), 0)

    def test_following_yourself_is_refused_with_a_sentence(self):
        response = self.client.post(reverse("connections:user-follow", args=["bello"]),
                                    {"next": self.feed}, follow=True)
        self.assertEqual(Follow.objects.count(), 0)
        self.assertContains(response, "You cannot follow yourself")

    def test_the_follow_button_is_absent_from_your_own_row(self):
        body = self.client.get(reverse("search:search"), {"q": "bello"}).content.decode()
        self.assertNotIn(reverse("connections:user-follow", args=["bello"]), body)


class ProfileConnectionTests(ConnectionActionTestCase):

    def test_the_followers_and_following_links_go_to_different_tabs(self):
        """They were the same bare URL, and `connections` defaults to
        followers — so "following" showed you followers."""
        body = self.client.get(reverse("accounts:user-profile", args=["asha"])).content.decode()
        base = reverse("connections:connections", args=["asha"])
        self.assertIn(f'href="{base}?tab=followers"', body)
        self.assertIn(f'href="{base}?tab=following"', body)

    def test_the_following_tab_lists_who_they_follow(self):
        third = User.objects.create_user("menuka", password="pw")
        Follow.objects.create(follower=self.other, following=third)

        body = self.client.get(reverse("connections:connections", args=["asha"]),
                               {"tab": "following"}).content.decode()

        self.assertIn("menuka", body)

    def test_the_active_tab_follows_the_url(self):
        body = self.client.get(reverse("accounts:user-profile", args=["asha"]),
                               {"tab": "likes"}).content.decode()
        self.assertIn('class="tab tab-active" href="?tab=likes"', body)
