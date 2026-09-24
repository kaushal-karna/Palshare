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

from .models import Comment, Media, Message, Post
from .services import attach_media, reaction_summary

from accounts.serializers import AuthorSerializer

User = get_user_model()



class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ["id", "kind", "alt", "file"]


class PostSerializer(serializers.ModelSerializer):
    """Matches `post` in demo.py — the contract the templates already read."""

    author = AuthorSerializer(read_only=True)
    media = MediaSerializer(many=True, read_only=True)
    likes = serializers.IntegerField(source="like_count", read_only=True)
    comments = serializers.IntegerField(source="comment_count", read_only=True)
    # Read straight off the annotations `visible_posts()` adds. A
    # SerializerMethodField that queries is a query per row, and a feed is
    # nothing but rows.
    liked = serializers.BooleanField(read_only=True, default=False)
    saved = serializers.BooleanField(read_only=True, default=False)
    shares = serializers.IntegerField(source="share_count", read_only=True)
    shared = serializers.BooleanField(read_only=True, default=False)
    # `created_at` is a timestamp for machines; `age` is a string for people.
    # One name for both is how a UI ends up printing an ISO 8601 string at a
    # human.
    age = serializers.SerializerMethodField()
    # Read off the `reactions` prefetch, not queried — see `reaction_summary`.
    reactions = serializers.SerializerMethodField()
    # `media` above is the output shape and is read-only, so uploading needs a
    # second field. The name differs from the HTML form's `media` on purpose:
    # one is a list of stored rows, the other is a list of incoming files, and
    # giving both the same name is how a serializer ends up trying to write to
    # its own output. Send it as multipart, one `upload` part per file.
    upload = serializers.ListField(
        child=serializers.FileField(), write_only=True, required=False,
        help_text="Up to four image or video files, sent as multipart/form-data.",
    )

    class Meta:
        model = Post
        fields = ["id", "author", "text", "media", "upload", "followers_only",
                  "likes", "comments", "shares", "reactions",
                  "liked", "saved", "shared",
                  "age", "created_at", "updated_at"]
        # Everything the server owns. `author` is not in this list because it
        # is not in `fields` as a writable field at all — it is nested and
        # read-only, and the view sets it from the credential.
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_age(self, post) -> str:
        return f"{timesince(post.created_at)} ago"

    def get_reactions(self, post) -> list:
        request = self.context.get("request")
        return reaction_summary(post, request.user if request else None)

    def create(self, validated_data):
        uploads = validated_data.pop("upload", [])
        with transaction.atomic():
            post = super().create(validated_data)
            self._attach(post, uploads)
        return post

    def update(self, instance, validated_data):
        uploads = validated_data.pop("upload", [])
        with transaction.atomic():
            post = super().update(instance, validated_data)
            self._attach(post, uploads)
        return post

    def _attach(self, post, uploads):
        """Same write rule as the page, translated into DRF's error type.

        `services.attach_media` raises Django's ValidationError, which DRF does
        not recognise — uncaught, a rejected file is a 500 instead of the 400 it
        is. The rule itself is not restated here, only the exception.
        """
        try:
            attach_media(post, uploads)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"upload": exc.messages})


class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    age = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    likes = serializers.IntegerField(source="like_count", read_only=True)
    # Read off the annotation `visible_comments()` adds, like the feed's.
    liked = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Comment
        fields = ["id", "post", "author", "text", "age", "likes", "liked", "parent", "replies"]
        read_only_fields = ["id"]

    def get_age(self, comment) -> str:
        return f"{timesince(comment.created_at)} ago"

    def get_replies(self, comment) -> list:
        # One level, and no deeper: `_comment.html` renders replies inline and
        # does not recurse, so neither does this.
        if comment.parent_id is not None:
            return []
        return CommentSerializer(comment.replies.all(), many=True,
                                 context=self.context).data

    def validate_parent(self, parent):
        """Replies go one level deep. The model allows more; we do not."""
        if parent and parent.parent_id is not None:
            raise serializers.ValidationError("Reply to the comment, not to a reply.")
        return parent


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
