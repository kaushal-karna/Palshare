from django.conf import settings
from django.db import models

from posts.models import Comment, Post


class Profile(models.Model):
    """Everything about a user that `auth.User` does not already hold.

    A OneToOne rather than a custom user model: swapping `AUTH_USER_MODEL`
    after the first migration is a rewrite, and this project is twelve hours
    old. `related_name="profile"` makes it `request.user.profile`.
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="legacy_profile")
    bio = models.TextField(blank=True)
    # FileField, not ImageField: ImageField needs Pillow, and this project has
    # gone ten days without adding a dependency. The extension allowlist in
    # `validate_upload` is the validation ImageField would have given us, and
    # it is validation the person who wrote it understands.
    avatar = models.FileField(upload_to="avatars/", blank=True, null=True)
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username













class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name="following")
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="one_follow_per_pair"),
            # Nobody follows themselves. Cheaper here than in every view that
            # creates a Follow.
            models.CheckConstraint(condition=~models.Q(follower=models.F("following")),
                                   name="no_self_follow"),
        ]


class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="conversations")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE,
                                     related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name="sent_messages")
    text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    # Both nullable rather than a boolean: "when" answers "whether" too, and
    # the thread shows the time an edit happened.
    edited_at = models.DateTimeField(null=True, blank=True)
    # Unsending is a soft delete. The row stays so the thread keeps its shape
    # and the other person sees that something was taken back rather than a
    # conversation that silently reads differently than they remember. The
    # text itself is cleared on the way out — an unsent message the server
    # still stores is not unsent.
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["sent_at"]

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    @property
    def is_edited(self):
        return self.edited_at is not None

# Temporary compatibility imports during domain extraction.
from interactions.models import (
    CommentLike,
    Like,
    Reaction,
    Save,
    Share,
)
