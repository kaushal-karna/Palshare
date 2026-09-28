from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from rest_framework.test import APITestCase

from accounts.models import Profile
from connections.models import Follow


User = get_user_model()

PASSWORD = "lab-passphrase-2026"


class ApiTestCase(APITestCase):
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
        self.asha_profile = Profile.objects.get(user=self.asha)
        self.bello_profile = Profile.objects.get(user=self.bello)
        self.client.force_authenticate(user=self.asha)


class FollowApiTests(ApiTestCase):
    def test_follow_is_idempotent(self):
        for _ in range(3):
            response = self.client.post("/api/palshare/users/bello/follow/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, {"following": True})
        self.assertEqual(Follow.objects.count(), 1)

    def test_you_cannot_follow_yourself(self):
        """The constraint is the guarantee; the view is the error message."""
        response = self.client.post("/api/palshare/users/asha/follow/")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "You cannot follow yourself.")

    def test_and_the_database_refuses_it_too(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Follow.objects.create(follower=self.asha, following=self.asha)

    def test_unfollow(self):
        self.client.post("/api/palshare/users/bello/follow/")
        response = self.client.post("/api/palshare/users/bello/unfollow/")
        self.assertEqual(response.data, {"following": False})
        self.assertEqual(Follow.objects.count(), 0)

    def test_a_profile_is_addressed_by_username(self):
        response = self.client.get("/api/palshare/users/bello/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "bello")
        self.assertFalse(response.data["is_following"])
