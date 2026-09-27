"""Models for the Connections domain."""

from django.db import models
from django.conf import settings


class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="following")
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "palshare"
        db_table = "palshare_follow"
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="one_follow_per_pair"),
            # Nobody follows themselves. Cheaper here than in every view that
            # creates a Follow.
            models.CheckConstraint(condition=~models.Q(follower=models.F("following")),
                                name="no_self_follow"),
        ]
