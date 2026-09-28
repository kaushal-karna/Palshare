"""Posts HTML views."""


from django.contrib import messages

from django.contrib.auth.decorators import login_required

from django.db import transaction

from django.core.exceptions import ValidationError

from django.core.paginator import Paginator

from django.http import HttpResponseForbidden

from django.shortcuts import get_object_or_404, redirect, render

from django.views.decorators.http import require_POST, require_http_methods

from posts.models import Comment, Post

from connections.models import Follow

from .services import (
    add_comment,
    attach_media,

)

from posts.queries import (
    saved_posts,
    visible_comments,
    visible_posts,
)

from posts.serializers import (
    CommentSerializer,
    PostSerializer,
)



PAGE_SIZE = 20

signed_in = login_required(login_url="accounts:login")


from common.web import shell


def posts_page(request, queryset):
    """One page of posts, serialized, plus the `page_obj` the pager reads."""
    page = Paginator(queryset, PAGE_SIZE).get_page(request.GET.get("page"))
    return {
        "posts": PostSerializer(page.object_list, many=True,
                                context={"request": request}).data,
        "page_obj": page,
    }


@signed_in
@require_http_methods(["GET", "POST"])
def feed(request):
    """The composer at the top of this page posts back to this URL.

    `_composer.html` is included with `action=""`, which means "this page" —
    so the POST arrives here and the redirect afterwards is what stops a
    refresh from posting twice.
    """
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        # `_composer.html` has had an "Add media" file input since hour one and
        # this handler read only `text`, so anything attached here was dropped
        # on the floor without a word. Same rule as `post_create`.
        uploads = request.FILES.getlist("media")
        if text or uploads:
            try:
                with transaction.atomic():
                    post = Post.objects.create(author=request.user, text=text)
                    attach_media(post, uploads)
            except ValidationError as exc:
                for message in exc.messages:
                    messages.error(request, message)
        return redirect("palshare:feed")

    posts = visible_posts(request.user)
    if request.GET.get("filter") == "following":
        # The tab says Following, so it means posts by people you follow —
        # not "everything except mine", which is what this used to do.
        posts = posts.filter(author__in=Follow.objects.filter(follower=request.user)
                            .values("following"))
    return render(request, "posts/feed.html",
                  shell(request, active="feed", **posts_page(request, posts)))


@signed_in
@require_http_methods(["GET", "POST"])
def post_create(request):
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        # `getlist`, not `request.FILES["media"]`: the input is `multiple`, and
        # the dict access silently returns the last file of four.
        uploads = request.FILES.getlist("media")
        if text or uploads:
            try:
                # The post and its files are one write. Without the atomic
                # block a rejected file leaves an empty post behind, which is
                # the user having posted something they did not write.
                with transaction.atomic():
                    post = Post.objects.create(
                        author=request.user,
                        text=text,
                        followers_only=bool(request.POST.get("private")),
                    )
                    attach_media(post, uploads)
            except ValidationError as exc:
                for message in exc.messages:
                    messages.error(request, message)
            else:
                return redirect("palshare:post-detail", pk=post.pk)
        else:
            # A photo with no caption is a post. Empty is not.
            messages.error(request, "A post needs some text or a file.")
    return render(request, "posts/post_form.html",
                shell(request, heading="New post"))


@signed_in
@require_http_methods(["GET", "POST"])
def post_edit(request, pk):
    # `visible_posts`, not `Post.objects`: a post you cannot see is a 404, not
    # a 403 — the second one confirms the row exists.
    post = get_object_or_404(visible_posts(request.user), pk=pk)
    if post.author_id != request.user.id:
        # Day 10's rule, on the HTML side. `IsAuthorOrReadOnly` says the same
        # thing to the API.
        return HttpResponseForbidden("You can only change things you created.")
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        uploads = request.FILES.getlist("media")
        if text or uploads or post.media.exists():
            try:
                with transaction.atomic():
                    post.text = text
                    post.followers_only = bool(request.POST.get("private"))
                    post.save(update_fields=["text", "followers_only", "updated_at"])
                    # Editing adds files, it does not replace them: removing one
                    # is a different action and needs its own control.
                    attach_media(post, uploads)
            except ValidationError as exc:
                for message in exc.messages:
                    messages.error(request, message)
            else:
                return redirect("palshare:post-detail", pk=post.pk)
        else:
            messages.error(request, "A post needs some text or a file.")
    return render(request, "posts/post_form.html", shell(
        request,
        heading="Edit post",
        post=PostSerializer(post, context={"request": request}).data,
    ))


@signed_in
@require_http_methods(["GET", "POST"])
def post_detail(request, pk):
    post = get_object_or_404(visible_posts(request.user), pk=pk)
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        if text:
            # `parent` arrives from the Reply form under each comment. The
            # service refuses to nest past one level; the model cannot.
            parent = None
            parent_id = request.POST.get("parent")
            if parent_id:
                parent = get_object_or_404(Comment, pk=parent_id, post=post)
            add_comment(request.user, post, text, parent=parent)
        return redirect("palshare:post-detail", pk=post.pk)

    comments = visible_comments(request.user, post)
    return render(request, "posts/post_detail.html", shell(
        request,
        post=PostSerializer(post, context={"request": request}).data,
        comments=CommentSerializer(comments, many=True,
                                context={"request": request}).data,
    ))


@signed_in
def saved(request):
    return render(request, "palshare/saved.html", shell(
        request, active="saved", **posts_page(request, saved_posts(request.user))))
