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
