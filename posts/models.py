from django.conf import settings
from django.db import models


class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    text = models.TextField()
    followers_only = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "palshare_post"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author}: {self.text[:40]}"


class Media(models.Model):
    KIND = [
        ("image", "Image"),
        ("video", "Video"),
    ]

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="media",
    )
    file = models.FileField(upload_to="posts/%Y/%m/")
    kind = models.CharField(
        max_length=5,
        choices=KIND,
        default="image",
    )
    alt = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "palshare_media"
