"""Views for external integrations such as the AI assistant."""

from django.conf import settings
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from common.web import shell, signed_in
from .services import ask_assistant


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

    return render(request, "integrations/assistant.html",
                  shell(request, active="assistant", turns=turns, error=error))
