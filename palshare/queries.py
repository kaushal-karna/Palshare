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
from .models import CommentLike, Conversation, Follow, Like, Save, Share

User = get_user_model()








def people(viewer, queryset=None):
    """Users, annotated with whether `viewer` already follows each one.

    The annotation is the same trick `visible_posts` plays with `liked`: a
    per-viewer fact computed for the whole page in the query that fetches it,
    rather than one query per row inside a serializer.
    """
    queryset = User.objects.all() if queryset is None else queryset
    # `select_related`, because every row serializer reads `profile.bio`, and a
    # OneToOne followed per row is the same N+1 as any other — it is just
    # spelled as an attribute access instead of a query.
    return queryset.select_related("profile").annotate(
        is_following=Exists(Follow.objects.filter(follower=viewer, following=OuterRef("pk"))),
    )


def suggestions_for(user, limit=3):
    """The right rail: people this person is not following yet, and not themselves."""
    followed = Follow.objects.filter(follower=user).values("following")
    return people(user, User.objects.exclude(pk=user.pk).exclude(pk__in=followed))[:limit]


def conversations_for(me):
    """Every conversation `me` is in, newest first, with the two facts the
    inbox badge needs: the other participant and how many unread messages.

    `prefetch_related` then counting in Python, rather than a `.filter()` per
    row: the prefetch is two queries for the whole page, and re-filtering a
    prefetched relation throws the cache away and goes back to the database.
    """
    rows = []
    for conversation in (Conversation.objects
                         .filter(participants=me)
                         .prefetch_related("participants", "messages__sender")):
        others = [p for p in conversation.participants.all() if p.pk != me.pk]
        messages = list(conversation.messages.all())
        rows.append({
            "conversation": conversation,
            "other": others[0] if others else me,
            "last": messages[-1] if messages else None,
            "unread": sum(1 for m in messages
                          if m.read_at is None and m.sender_id != me.pk),
        })
    return rows


def search(user, q):
    q = q.strip()
    if len(q) < 2:
        # Two characters is not a search, it is a table scan. The page has an
        # empty state for exactly this.
        return {"query": q, "people": [], "posts": []}
    return {
        "query": q,
        # Last name was missing here, so searching a room full of people by
        # the half of their name they were introduced by found nobody. Bio is
        # in for the same reason: it is the only other text a person writes
        # about themselves.
        "people": people(user, User.objects.filter(
            Q(username__icontains=q) | Q(first_name__icontains=q)
            | Q(last_name__icontains=q) | Q(profile__bio__icontains=q)
        ).distinct())[:10],
        # `visible_posts`, not `Post.objects`: search is the classic way private
        # data leaks, because the detail page checks permissions and the search
        # does not.
        "posts": visible_posts(user).filter(text__icontains=q)[:20],
    }
# Temporary compatibility imports during domain extraction.
from posts.queries import (
    may_see_posts,
    saved_posts,
    visible_comments,
    visible_posts,
)
