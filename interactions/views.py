"""Web views for post and comment interactions."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from common.web import back, signed_in
from posts.models import Comment
from posts.queries import visible_posts
from interactions.services import (
    set_reaction,
    toggle_comment_like,
    toggle_like,
    toggle_save,
    toggle_share,
)


@signed_in
@require_POST
def post_like(request, pk):
    toggle_like(request.user, get_object_or_404(visible_posts(request.user), pk=pk))
    return back(request, "posts:feed")

@signed_in
@require_POST
def post_save(request, pk):
    toggle_save(request.user, get_object_or_404(visible_posts(request.user), pk=pk))
    return back(request, "posts:feed")

@signed_in
@require_POST
def post_share(request, pk):
    toggle_share(request.user, get_object_or_404(visible_posts(request.user), pk=pk))
    return back(request, "posts:feed")

@signed_in
@require_POST
def post_react(request, pk):
    """The emoji bar under a post. One reaction per person, and pressing the
    one you already picked takes it back."""
    post = get_object_or_404(visible_posts(request.user), pk=pk)
    try:
        set_reaction(request.user, post, request.POST.get("emoji") or None)
    except ValidationError as exc:
        for message in exc.messages:
            messages.error(request, message)
    return back(request, reverse("posts:post-detail", args=[post.pk]))

@signed_in
@require_POST
def comment_like(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    # You may only like a comment on a post you are allowed to read.
    get_object_or_404(visible_posts(request.user), pk=comment.post_id)
    toggle_comment_like(request.user, comment)
    return back(request, reverse("posts:post-detail", args=[comment.post_id]))
