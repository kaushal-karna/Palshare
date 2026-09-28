"""Visibility rules, written once.

Day 10 ended with the same rule written twice — once in a DRF `get_queryset`
and once in a plain view — because a permission class protects a DRF view and
nothing else. This module is the fix: both consumers import from here, so
"what may this person see" has exactly one definition.

Nothing in here takes a `request`. Every function takes a `user` and plain
arguments, which is what lets the API view and the page view call the same
function instead of each growing its own copy of the rule.
"""

from django.contrib.auth import get_user_model

from django.db.models import Exists, OuterRef, Q


from posts.models import Comment, Post
from messaging.models import Conversation
from connections.models import Follow
from interactions.models import CommentLike, Like, Save, Share

User = get_user_model()

















# Temporary compatibility export during domain extraction.
from messaging.queries import conversations_for

# Temporary compatibility export during domain extraction.
from connections.queries import people, suggestions_for

# Temporary compatibility exports during domain extraction.
from posts.queries import (
    visible_posts,
    saved_posts,
    may_see_posts,
    visible_comments,
)

# Temporary compatibility import during domain extraction.
from search.queries import search
