from django.contrib.auth import get_user_model

from django.db.models import Exists, OuterRef, Q

from posts.models import Comment, Post

from palshare.models import CommentLike, Conversation, Follow, Like, Save, Share

def visible_posts(user):
    """Posts `user` may see: their own, everything public, and followers-only
    posts by people they follow."""
    followed = Follow.objects.filter(follower=user).values("following")
    return (
        Post.objects
        # `author__profile` and not just `author`: every byline renders an
        # avatar, and the avatar reads `author.profile.avatar`. A OneToOne
        # followed per row is an N+1 spelled as an attribute access — the same
        # one `people()` already documents, one level down.
        .select_related("author", "author__profile")
        # `reactions` is prefetched, not annotated: five emoji would be five
        # correlated subqueries per row, and this is one query for the whole
        # page. The serializer counts them in Python, where counting five
        # things is free.
        .prefetch_related("media", "reactions")
        .annotate(
            liked=Exists(Like.objects.filter(user=user, post=OuterRef("pk"))),
            saved=Exists(Save.objects.filter(user=user, post=OuterRef("pk"))),
            shared=Exists(Share.objects.filter(user=user, post=OuterRef("pk"))),
        )
        .filter(Q(author=user) | Q(followers_only=False) | Q(author__in=followed))
    )

def saved_posts(user):
    """The saved page is the feed, filtered to rows this person starred.

    Still built on `visible_posts`: unfollowing somebody should hide their
    followers-only posts everywhere, including from a list you saved them to.
    """
    return visible_posts(user).filter(saves__user=user)

def may_see_posts(viewer, owner):
    """A private account shows its posts to itself and its followers, nobody else."""
    if viewer == owner:
        return True
    if not owner.is_private:
        return True
    return Follow.objects.filter(follower=viewer, following=owner).exists()

def visible_comments(user, post):
    """A post's top-level comments, with the viewer's own likes annotated.

    Same `Exists()` trick as the feed: `liked` is a per-viewer fact, so it is
    computed for the whole thread in the query that fetches it rather than one
    query per comment.
    """
    return (Comment.objects
            .filter(post=post, parent__isnull=True)
            .select_related("author", "author__profile")
            .prefetch_related("replies__author", "replies__author__profile")
            .annotate(liked=Exists(CommentLike.objects.filter(user=user,
                                                              comment=OuterRef("pk")))))
