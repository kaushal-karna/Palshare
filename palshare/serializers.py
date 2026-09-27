"""One shape per thing, defined once and consumed twice.

The templates read `post.author.name`, `post.likes`, `post.liked`, `post.age`.
The models have `author.first_name`, `like_count`, no `liked` at all, and a
`created_at` that is a timestamp rather than a phrase. The serializers close
that gap — and because `views.py` renders through them too, the page and the
API cannot drift apart.

`demo.py` is the contract these match. Read the two side by side.
"""

from django.contrib.auth import get_user_model

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.template.defaultfilters import date as date_filter
from django.utils.timesince import timesince
from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from posts.models import Comment, Media,  Post
from messaging.models import Message
from .services import attach_media, reaction_summary

from accounts.serializers import AuthorSerializer

User = get_user_model()









class MessageSerializer(serializers.ModelSerializer):
    """`mine` comes from the server, on purpose.

    `thread.html` says so in its own comment: working it out in the template by
    comparing usernames breaks the day somebody changes their display name.
    """

    mine = serializers.SerializerMethodField()
    sent_at = serializers.SerializerMethodField()
    # `deleted` and `edited` are booleans for the template, not timestamps:
    # the thread shows a state, not a date, and `{% if message.deleted %}`
    # reads better than a null check on a formatted string.
    deleted = serializers.BooleanField(source="is_deleted", read_only=True)
    edited = serializers.BooleanField(source="is_edited", read_only=True)

    class Meta:
        model = Message
        fields = ["id", "mine", "text", "sent_at", "deleted", "edited"]

    def get_mine(self, message) -> bool:
        request = self.context.get("request")
        return bool(request and message.sender_id == request.user.pk)

    def get_sent_at(self, message) -> str:
        return date_filter(message.sent_at, "H:i")

# Temporary compatibility imports during domain extraction.
from posts.serializers import (
    CommentSerializer,
    MediaSerializer,
    PostSerializer,
)
