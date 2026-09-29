from django.contrib.auth import get_user_model

from django.test import TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch

from accounts.models import Profile


User = get_user_model()


class IntegrationTestCase(TestCase):
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


class AssistantTests(IntegrationTestCase):

    @override_settings(NVIDIA_API_KEY="")
    def test_an_unconfigured_assistant_says_so_and_names_the_key(self):
        """It was not broken, it was unconfigured — and the page said
        "unavailable, try again", which is advice that never comes true."""
        response = self.client.post(reverse("integrations:assistant"), {"prompt": "hi"})
        self.assertContains(response, "NVIDIA_API_KEY")

    @override_settings(NVIDIA_API_KEY="a-key-that-will-not-answer")
    @patch("integrations.views.ask_assistant", return_value=None)
    def test_a_configured_assistant_that_fails_gets_the_other_message(self, asked):
        """Patched, not called for real. A test that reaches the internet fails
        on a train, and this one was posting to NVIDIA on every run."""
        response = self.client.post(reverse("integrations:assistant"), {"prompt": "hi"})
        self.assertContains(response, "unavailable right now")
        self.assertNotContains(response, "NVIDIA_API_KEY")
        self.assertTrue(asked.called)

    @override_settings(NVIDIA_API_KEY="a-key-that-works")
    @patch("integrations.views.ask_assistant", return_value="Try: golden hour, no filter.")
    def test_a_working_assistant_puts_the_reply_in_the_thread(self, asked):
        response = self.client.post(reverse("integrations:assistant"),
                                    {"prompt": "caption this"}, follow=True)
        self.assertContains(response, "golden hour")
        asked.assert_called_once_with("caption this")

    @override_settings(NVIDIA_API_KEY="")
    def test_your_own_prompt_is_kept_even_when_the_model_does_not_answer(self):
        self.client.post(reverse("integrations:assistant"), {"prompt": "write me a caption"})
        body = self.client.get(reverse("integrations:assistant")).content.decode()
        self.assertIn("write me a caption", body)
