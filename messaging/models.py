"""Models for the Messaging domain."""

from django.conf import settings
from django.db import models


class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="conversations")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "messaging_conversation"
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
        db_table = "messaging_message"
        ordering = ["sent_at"]

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    @property
    def is_edited(self):
        return self.edited_at is not None

from interactions.models import CommentLike, Like, Reaction, Save, Share
