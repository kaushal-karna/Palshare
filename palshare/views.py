"""The HTML half of the app. The other half is `api.py`.

Every page renders through the serializers in `serializers.py`, so the page and
the API cannot disagree about what a post is. The usual alternative — pass the
queryset to the template and let it call model attributes — works fine until
the API adds a field the page needs, and then there are two definitions.

Not one template was changed to make these views work. The URL names, the
context keys and the markup are all exactly what the shell was built with;
`demo.py` said what the shapes were, and these views produce them.
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model

from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.template.defaultfilters import date as date_filter
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST, require_http_methods
from .view_helpers import back, signed_in
from connections.views import connections, user_follow

from .integrations import ask_assistant, current_weather

from accounts.models import Profile
from accounts.services import set_avatar

from accounts.serializers import (
    PersonRowSerializer,
    PersonSerializer,
)

from posts.models import Comment, Post
from interactions.models import Reaction
from messaging.models import Conversation, Message
from connections.models import Follow
from .services import (
    add_comment,
    attach_media,
    edit_message,
    set_reaction,
    unsend_message,
    conversation_with,
    toggle_comment_like,
    toggle_follow,
    toggle_like,
    toggle_save,
    toggle_share,
)
from .queries import (
    conversations_for,
    may_see_posts,
    people,
    saved_posts,
    search as search_query,
    visible_comments,
    suggestions_for,
    visible_posts,
)

from accounts.serializers import (
    PersonRowSerializer,
    PersonSerializer,
    display_name,
    initial,
)

from .serializers import (
    CommentSerializer,
    MessageSerializer,
    PostSerializer,
)

User = get_user_model()

PAGE_SIZE = 20

# `@login_required` alone would send people to `settings.LOGIN_URL`, which is
# the admin login — a different app's front door. PalShare has its own.




def profile_of(user):
    """Every user in this app has a Profile; some of them do not know it yet.

    `get_or_create` rather than a signal: a signal fires on every `User` save
    in the whole project, including the blog app's, and this is the only place
    that needs the row.
    """
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile







# --- feed and posts -------------------------------------------------------

@signed_in
@require_http_methods(["GET", "POST"])


@signed_in
@require_http_methods(["GET", "POST"])


@signed_in
@require_http_methods(["GET", "POST"])


@signed_in
@require_http_methods(["GET", "POST"])


@signed_in
def saved(request):
    return render(request, "palshare/saved.html", shell(
        request, active="saved", **posts_page(request, saved_posts(request.user))))


# --- profile and the follow graph ----------------------------------------

@signed_in
def profile(request, username):
    # Fetched through `people()` so the header's Follow button reads the same
    # annotation every user row in the app reads, rather than its own query.
    owner = get_object_or_404(people(request.user), username=username)
    profile_of(owner)  # `may_see_posts` reads `owner.profile`

    # The three tabs were `?tab=` links that no view read, so Media and Likes
    # both rendered the Posts list and the active tab never moved.
    tab = request.GET.get("tab", "posts")
    if tab not in {"posts", "media", "likes"}:
        tab = "posts"

    context = shell(request, active="profile", posts=[], tab=tab,
                    profile=PersonSerializer(owner, context={"request": request}).data)
    if may_see_posts(request.user, owner):
        posts = visible_posts(request.user)
        if tab == "media":
            # `media__isnull=False` alone returns one row per attached file.
            posts = posts.filter(author=owner, media__isnull=False).distinct()
        elif tab == "likes":
            # Posts this person liked, not posts of theirs that were liked —
            # which is what the word means everywhere else it appears in a
            # social app.
            posts = posts.filter(likes__user=owner)
        else:
            posts = posts.filter(author=owner)
        context.update(posts_page(request, posts))
    return render(request, "palshare/profile.html", context)


@signed_in


# --- search ---------------------------------------------------------------

@signed_in
def search(request):
    results = search_query(request.user, request.GET.get("q", ""))
    return render(request, "palshare/search.html", shell(
        request,
        active="search",
        query=results["query"],
        people=PersonRowSerializer(results["people"], many=True,
                                   context={"request": request}).data,
        posts=PostSerializer(results["posts"], many=True,
                             context={"request": request}).data,
    ))


# --- messaging ------------------------------------------------------------

def when(moment):
    """A time for today, a date for anything older. `demo.py` showed both."""
    local = timezone.localtime(moment)
    if local.date() == timezone.localdate():
        return date_filter(local, "H:i")
    return date_filter(local, "j M")


@signed_in
def inbox(request):
    conversations = [{
        "id": row["conversation"].pk,
        "person": PersonRowSerializer(row["other"], context={"request": request}).data,
        "last_message": row["last"].text if row["last"] else "",
        "unread": row["unread"],
        "updated_at": when(row["conversation"].updated_at),
    } for row in conversations_for(request.user)]
    return render(request, "palshare/inbox.html",
                  shell(request, active="inbox", conversations=conversations))


@signed_in
@require_http_methods(["GET", "POST"])
def thread(request, pk):
    # Filtering by participant is the permission check: a conversation you are
    # not in does not exist as far as this view is concerned.
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user).prefetch_related("participants"),
        pk=pk)
    other = next((p for p in conversation.participants.all() if p.pk != request.user.pk),
                 request.user)

    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        if text:
            Message.objects.create(conversation=conversation, sender=request.user, text=text)
            # `Meta.ordering` sorts the inbox by `updated_at`, which only means
            # anything if sending a message touches it.
            conversation.save(update_fields=["updated_at"])
        return redirect("palshare:thread", pk=conversation.pk)

    unread = conversation.messages.exclude(sender=request.user).filter(read_at__isnull=True)
    unread.update(read_at=timezone.now())

    thread_messages = conversation.messages.select_related("sender")
    return render(request, "palshare/thread.html", shell(
        request,
        active="inbox",
        # `?edit=<id>` opens one bubble as a form. A query parameter rather
        # than JavaScript, for the same reason every other control here is a
        # form: it survives a reload and it works with the keyboard.
        editing=request.GET.get("edit", ""),
        emoji=[value for value, _ in Reaction.EMOJI],
        conversation={
            "id": conversation.pk,
            "person": PersonRowSerializer(other, context={"request": request}).data,
        },
        # Never `messages`: django.contrib.messages owns that name, and
        # base.html renders whatever is in it as flash messages.
        thread_messages=MessageSerializer(thread_messages, many=True,
                                          context={"request": request}).data,
    ))


# --- integrations ---------------------------------------------------------

@signed_in
@require_http_methods(["GET", "POST"])
def assistant(request):
    """The conversation lives in the session, not the database.

    Nothing in the schema stores assistant turns, and inventing a table for a
    demo feature is how a schema grows things nobody maintains.
    """
    turns = request.session.get("assistant_turns", [])
    error = None

    if request.method == "POST":
        prompt = request.POST.get("prompt", "").strip()
        if prompt:
            turns = turns + [{"role": "you", "text": prompt}]
            reply = ask_assistant(prompt)
            if reply is None:
                # Two different failures wore one message, so "it does not
                # work" was indistinguishable from "nobody has configured it".
                # The first is a five-second fix and the page now says so.
                if not settings.NVIDIA_API_KEY:
                    error = ("The assistant has no API key. Set NVIDIA_API_KEY in .env "
                             "and restart the server — see .env.example.")
                else:
                    error = "The assistant is unavailable right now. Try again in a moment."
            else:
                turns.append({"role": "assistant", "text": reply})
            request.session["assistant_turns"] = turns[-20:]

    return render(request, "palshare/assistant.html",
                  shell(request, active="assistant", turns=turns, error=error))


# --- the one-row-or-none actions -----------------------------------------
#
# Seven controls in the shell were `<button type="button">` with nothing behind
# them. They are real forms now, and each one posts here, flips a row and
# returns you to the page you were on. No JavaScript: a form works with the
# keyboard, with the back button, and with JavaScript switched off, and the
# whole app already reloads on every write anyway.

@signed_in
@require_POST
def post_like(request, pk):
    toggle_like(request.user, get_object_or_404(visible_posts(request.user), pk=pk))
    return back(request, "palshare:feed")


@signed_in
@require_POST
def post_save(request, pk):
    toggle_save(request.user, get_object_or_404(visible_posts(request.user), pk=pk))
    return back(request, "palshare:feed")


@signed_in
@require_POST
def post_share(request, pk):
    toggle_share(request.user, get_object_or_404(visible_posts(request.user), pk=pk))
    return back(request, "palshare:feed")


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
    return back(request, reverse("palshare:post-detail", args=[post.pk]))


# --- messages you can take back -------------------------------------------
#
# Both of these are POST-only and both re-check the sender in `services.py`,
# not here: "you may only change your own message" is a rule about messages,
# and a rule that lives in a view is a rule the API gets to disagree with.

@signed_in
@require_POST
def message_edit(request, pk):
    message = get_object_or_404(
        Message.objects.filter(conversation__participants=request.user), pk=pk)
    try:
        edit_message(request.user, message, request.POST.get("text", ""))
    except ValidationError as exc:
        for text in exc.messages:
            messages.error(request, text)
    return redirect("palshare:thread", pk=message.conversation_id)


@signed_in
@require_POST
def message_unsend(request, pk):
    message = get_object_or_404(
        Message.objects.filter(conversation__participants=request.user), pk=pk)
    try:
        unsend_message(request.user, message)
    except ValidationError as exc:
        for text in exc.messages:
            messages.error(request, text)
    return redirect("palshare:thread", pk=message.conversation_id)


@signed_in
@require_POST
def comment_like(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    # You may only like a comment on a post you are allowed to read.
    get_object_or_404(visible_posts(request.user), pk=comment.post_id)
    toggle_comment_like(request.user, comment)
    return back(request, reverse("palshare:post-detail", args=[comment.post_id]))


@signed_in
@require_POST


@signed_in
@require_POST
def message_user(request, username):
    """The profile's Message button. Opens the one conversation with that
    person, creating it on first use."""
    other = get_object_or_404(User, username=username)
    if other == request.user:
        messages.error(request, "You cannot message yourself.")
        return redirect("palshare:inbox")
    conversation = conversation_with(request.user, other)
    return redirect("palshare:thread", pk=conversation.pk)

# Temporary compatibility imports during domain extraction.
from .view_helpers import shell
from posts.views import (
    feed,
    post_create,
    post_detail,
    post_edit,
    posts_page,
)

# Temporary compatibility imports during domain extraction.
