from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

"""Shared presentation helpers for HTML views."""





def shell(request, **context):
    """The three things every signed-in page needs: the header, the nav and
    the right rail.

    `urls.py` used to set these from `demo.py`, one page at a time. If a fourth
    thing turns up, this becomes a context processor.
    """
    user = request.user
    # Serialized rather than hand-built. The hand-built dict had three of the
    # four keys `_avatar.html` reads, so the header and the composer showed
    # your initial even after you had uploaded a picture — while every other
    # avatar on the same page showed the picture. A shape assembled twice is a
    # shape that disagrees with itself.
    # `None` when the key is missing or the API is down. The widget has an
    # empty state and renders it.
    # The one palette, defined on the model, handed to every template that
    # offers emoji — the picker and the reaction bar read the same list.j
    return context


def back(request, fallback):
    """Return to the page the button was on.

    `url_has_allowed_host_and_scheme` is not optional: without it, `?next=` is
    an open redirect, and an open redirect on a login-walled page is how a
    phishing link borrows your domain.
    """
    target = request.POST.get("next") or request.META.get("HTTP_REFERER", "")
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()},
                                                  require_https=request.is_secure()):
        return redirect(target)
    return redirect(fallback)


signed_in = login_required(login_url="accounts:login")
