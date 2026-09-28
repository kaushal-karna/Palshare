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










# Temporary compatibility imports during domain extraction.
from posts.serializers import (
    CommentSerializer,
    MediaSerializer,
    PostSerializer,
)

# Temporary compatibility export during domain extraction.
from messaging.serializers import MessageSerializer
