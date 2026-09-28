from django.conf import settings
from django.db import models

from posts.models import Comment, Post


class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                            related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # The database enforces "one like per person per post". Checking in
        # Python instead loses the race between two taps on a slow connection.
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="one_like_per_user")]


class Save(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                            related_name="saves")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="saves")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="one_save_per_user")]


class Share(models.Model):
    """The third of the three one-row-or-none features.

    `_post_card.html` has been rendering a share count since hour one and
    nothing was storing it, so the number was a literal zero. One share per
    person per post, no quote-post semantics.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                            related_name="shares")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="shares")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="one_share_per_user")]


class Reaction(models.Model):
    """One emoji per person per post, and changing it replaces it.

    The same shape as `Like` with one extra column, and deliberately *not* a
    replacement for it: `♥` is its own control in every card, the API has a
    `like` action, and a counter cache behind it. A reaction is the second,
    softer thing you can say about a post, not a rename of the first.

    The palette is a fixed list rather than free text. An open emoji column is
    an open text column — someone reacts with an essay, or with an emoji that
    renders as a box on half the machines in the room.
    """

    EMOJI = [
        ("\U0001f44d", "Thumbs up"),
        ("\u2764\ufe0f", "Heart"),
        ("\U0001f602", "Laugh"),
        ("\U0001f62e", "Surprise"),
        ("\U0001f389", "Celebrate"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                            related_name="reactions")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reactions")
    # `max_length` is characters, not bytes, and "❤️" is two of them: the heart
    # plus a variation selector. Four leaves room for a flag or a skin tone.
    emoji = models.CharField(max_length=4, choices=EMOJI)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "post"],
                                                name="one_reaction_per_user")]


class CommentLike(models.Model):
    """Same shape again, one level down. `_comment.html` has a Like button."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                            related_name="comment_likes")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "comment"],
                                                name="one_comment_like_per_user")]
