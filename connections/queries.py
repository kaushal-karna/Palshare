from django.contrib.auth import get_user_model

from django.db.models import Exists, OuterRef

from connections.models import Follow


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
