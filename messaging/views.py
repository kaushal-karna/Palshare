from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages

from django.views.decorators.http import require_http_methods, require_POST

from accounts.models import User
from accounts.serializers import PersonRowSerializer

from interactions.models import Reaction

from messaging.models import Conversation, Message
from messaging.queries import conversations_for
from messaging.serializers import MessageSerializer
from messaging.services import conversation_with, edit_message, unsend_message

from palshare.serializers import date_filter
from palshare.view_helpers import back, shell, signed_in


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
    return render(request, "messaging/inbox.html",
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
    return render(request, "messaging/thread.html", shell(
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

@signed_in
@require_POST


@signed_in
@require_POST


@signed_in
@require_POST


@signed_in
@require_POST


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
