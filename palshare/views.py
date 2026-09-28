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
from accounts.views import user_profile as profile
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
    unsend_message,
    conversation_with,
    toggle_follow,
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





# --- feed and posts -------------------------------------------------------

@signed_in
@require_http_methods(["GET", "POST"])


@signed_in
@require_http_methods(["GET", "POST"])


@signed_in
@require_http_methods(["GET", "POST"])


@signed_in
@require_http_methods(["GET", "POST"])




# --- search ---------------------------------------------------------------

# --- messaging ------------------------------------------------------------







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

# Temporary compatibility export during domain extraction.
from posts.views import saved

# Temporary compatibility import during domain extraction.
from search.views import search

# Temporary compatibility imports during domain extraction.
from messaging.views import (
    inbox,
    message_edit,
    message_unsend,
    message_user,
    thread,
)
