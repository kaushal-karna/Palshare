from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):
    email = models.EmailField(
        unique=True,
        null=True,
        blank=True,
        default=None,
    )

    is_verified = models.BooleanField(
        default=False
    )

    is_private = models.BooleanField(
        default=False
    )

    last_seen = models.DateTimeField(
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        if self.email == "":
            self.email = None
            super().save(*args,**kwargs)
    def __str__(self):
        return self.username


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    avatar = models.ImageField(
        upload_to="profiles/avatars/",
        blank=True,
        null=True,
    )

    cover_photo = models.ImageField(
        upload_to="profiles/covers",
        blank=True,
        null=True,
    )

    bio = models.TextField(
        max_length=500,
        blank=True
    )

    location = models.CharField(
        max_length=150,
        blank=True,
    )

    website = models.URLField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.user.username}'s profile"
