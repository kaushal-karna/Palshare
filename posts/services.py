from django.db.models import F

from posts.models import Comment, Media
from common.uploads import validate_uploads

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

def add_comment(user, post, text, parent=None):
    """One place that knows a comment bumps a counter and a reply cannot nest.

    The model allows any depth — a CheckConstraint cannot walk a tree — so the
    rule that replies go one level deep lives here and in the serializer.
    """
    if parent is not None and parent.parent_id is not None:
        parent = parent.parent  # a reply to a reply attaches to its top-level comment
    comment = Comment.objects.create(post=post, author=user, text=text, parent=parent)
    _bump(post, "comment_count", 1)
    return comment

def attach_media(post, uploads):
    """Store uploaded files against a post and return the new `Media` rows.

    Every file is validated before the first one is written, so a four-file
    post with one bad file stores nothing — a post that half-uploaded is worse
    to explain than one that did not upload at all.

    Raises `django.core.exceptions.ValidationError`. Callers translate it:
    the view turns it into `messages.error`, the serializer re-raises it as
    DRF's ValidationError so the API answers 400 rather than 500.

    One thing this cannot give you: the files are written to disk by
    `FileField.pre_save`, and a rolled-back transaction does not unwrite them.
    A failure after this point leaves bytes in MEDIA_ROOT with no row pointing
    at them. That is the normal Django trade-off, and the reason validation
    happens first rather than being discovered halfway through.
    """
    uploads = list(uploads)
    if not uploads:
        return []
    checked = validate_uploads(uploads, existing=post.media.count())
    return [Media.objects.create(post=post, file=upload, kind=kind)
            for upload, kind in checked]
