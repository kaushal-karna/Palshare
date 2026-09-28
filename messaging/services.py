from django.core.exceptions import ValidationError
from django.utils import timezone

from messaging.models import Conversation


def conversation_with(me, other):
    """The one conversation between two people, created on first message.

    Two ilter() calls, not one with two participants: a single filter on a
    ManyToMany matches rows with either participant. Chaining them means
    "has me AND has other".
    """
    existing = (
        Conversation.objects
        .filter(participants=me)
        .filter(participants=other)
        .first()
    )

    if existing:
        return existing

    conversation = Conversation.objects.create()
    conversation.participants.add(me, other)
    return conversation


def edit_message(user, message, text):
    """Change the text of a message you sent.

    You may only edit your own message, and you may not edit one already
    unsent. An edit is timestamped.
    """
    if message.sender_id != user.pk:
        raise ValidationError("You can only edit messages you sent.")

    if message.is_deleted:
        raise ValidationError("That message was unsent.")

    text = (text or "").strip()

    if not text:
        raise ValidationError("An edited message still needs some text.")

    message.text = text
    message.edited_at = timezone.now()
    message.save(update_fields=["text", "edited_at"])

    return message


def unsend_message(user, message):
    """Take back a message you sent.

    The message row remains so thread ordering is preserved, but the text is
    cleared and the message is marked as deleted.
    """
    if message.sender_id != user.pk:
        raise ValidationError("You can only unsend messages you sent.")

    if message.is_deleted:
        return message

    message.text = ""
    message.deleted_at = timezone.now()
    message.save(update_fields=["text", "deleted_at"])

    return message
