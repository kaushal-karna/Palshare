"""Business rules for likes, saves, shares, reactions and comment likes."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import F

from posts.models import Comment, Post

from interactions.models import (
    CommentLike,
    Like,
    Reaction,
    Save,
    Share,
)

def _bump(owner, field, by):
    """Move a counter cache, without letting it go negative.

    `F()` rather than `owner.field + 1`: two people liking at the same moment
    both read the same number and both write it back, and one of the likes
    disappears. The database can add; let it.
    """
    queryset = type(owner).objects.filter(pk=owner.pk)
    if by < 0:
        # A counter that has already drifted to zero must not wrap around into
        # four billion, which is what a PositiveIntegerField does on underflow.
        queryset = queryset.filter(**{f"{field}__gt": 0})
    queryset.update(**{field: F(field) + by})


def _add(model, owner, field, **lookup):
    """Create the row unless the unique constraint says it is already there."""
    try:
        # The savepoint is load-bearing: a constraint violation marks the whole
        # surrounding transaction as broken, so without one to roll back to,
        # catching IntegrityError buys nothing and the next query in the
        # request dies with TransactionManagementError.
        with transaction.atomic():
            model.objects.create(**lookup)
    except IntegrityError:
        return False  # the unique constraint did its job
    _bump(owner, field, 1)
    return True


def _remove(model, owner, field, **lookup):
    deleted, _ = model.objects.filter(**lookup).delete()
    if deleted:
        _bump(owner, field, -1)
    return bool(deleted)


def set_like(user, post, on):
    if on:
        _add(Like, post, "like_count", user=user, post=post)
    else:
        _remove(Like, post, "like_count", user=user, post=post)
    return on


def set_save(user, post, on):
    """No counter to move: nothing in the UI renders "saved by 12 people",
    so a save is a row and nothing else."""
    if on:
        try:
            with transaction.atomic():  # see `_add` for why the savepoint matters
                Save.objects.create(user=user, post=post)
        except IntegrityError:
            pass
    else:
        Save.objects.filter(user=user, post=post).delete()
    return on


def set_share(user, post, on):
    if on:
        _add(Share, post, "share_count", user=user, post=post)
    else:
        _remove(Share, post, "share_count", user=user, post=post)
    return on


def set_comment_like(user, comment, on):
    if on:
        _add(CommentLike, comment, "like_count", user=user, comment=comment)
    else:
        _remove(CommentLike, comment, "like_count", user=user, comment=comment)
    return on


def toggle_like(user, post):
    return set_like(user, post, not Like.objects.filter(user=user, post=post).exists())


def toggle_save(user, post):
    return set_save(user, post, not Save.objects.filter(user=user, post=post).exists())


def toggle_share(user, post):
    return set_share(user, post, not Share.objects.filter(user=user, post=post).exists())


def toggle_comment_like(user, comment):
    return set_comment_like(
        user, comment, not CommentLike.objects.filter(user=user, comment=comment).exists())


def set_reaction(user, post, emoji):
    """Set, change or clear this person's one reaction to a post.

    Three behaviours in one function because they are one behaviour from the
    user's side: pressing an emoji you already picked takes it back, pressing a
    different one moves your reaction, and `emoji=None` clears it. Everything
    returns the resulting emoji, or None, so the caller never has to re-read.

    `update_or_create` rather than delete-then-create: the unique constraint is
    on (user, post), and a delete/create pair is a window in which a double tap
    creates two rows.
    """
    valid = {value for value, _ in Reaction.EMOJI}
    if emoji is not None and emoji not in valid:
        # A fixed palette that only the template enforces is not a fixed
        # palette — this endpoint takes whatever a caller posts to it.
        raise ValidationError("That is not one of the reactions.")

    current = Reaction.objects.filter(user=user, post=post).first()
    if emoji is None or (current and current.emoji == emoji):
        Reaction.objects.filter(user=user, post=post).delete()
        return None
    Reaction.objects.update_or_create(user=user, post=post, defaults={"emoji": emoji})
    return emoji


def reaction_summary(post, user):
    """The whole palette with counts, for one post.

    Every emoji is returned, including the ones nobody picked, so the bar under
    a post has the same five buttons whether it has a thousand reactions or
    none. Reads the `reactions` prefetch rather than querying: called once per
    row of a feed, a query here would be the N+1 the prefetch exists to avoid.
    """
    rows = list(post.reactions.all())
    mine = next((r.emoji for r in rows if r.user_id == getattr(user, "pk", None)), None)
    counts = {}
    for reaction in rows:
        counts[reaction.emoji] = counts.get(reaction.emoji, 0) + 1
    return [{"emoji": emoji, "label": label, "count": counts.get(emoji, 0),
             "mine": mine == emoji}
            for emoji, label in Reaction.EMOJI]
