from django.contrib.auth import get_user_model
from django.db.models import Q

from connections.queries import people
from posts.queries import visible_posts


User = get_user_model()


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
