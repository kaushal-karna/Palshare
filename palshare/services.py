"""Shared business rules for Connections and Messaging.

Interaction state changes live in ``interactions.services``. This module
continues to provide the remaining connection and messaging service layer
during the domain extraction.
"""

from django.core.exceptions import ValidationError
from django.utils import timezone


from messaging.models import Conversation
from connections.models import Follow













def conversation_with(me, other):
    """The one conversation between two people, created on first message.

    Two `filter()` calls, not one with two participants: a single filter on a
    ManyToMany matches rows with *either* participant. Chaining them means
    "has me AND has other".
    """
    existing = (Conversation.objects
                .filter(participants=me)
                .filter(participants=other)
                .first())
    if existing:
        return existing
    conversation = Conversation.objects.create()
    conversation.participants.add(me, other)
    return conversation








def edit_message(user, message, text):
    """Change the text of a message you sent.

    Three rules, and the first two are the whole feature: you may only edit
    your own, and you may not edit one you already unsent. The third is that an
    edit is stamped, because a message that can change silently is a message
    the other person cannot trust.
    """
    if message.sender_id != user.pk:
        raise ValidationError("You can only edit messages you sent.")
    if message.is_deleted:
        raise ValidationError("That message was unsent.")
    text = (text or "").strip()
    if not text:
        # Emptying a message is unsending it, and unsending has its own
        # function that clears the text properly and says so in the thread.
        raise ValidationError("An edited message still needs some text.")
    message.text = text
    message.edited_at = timezone.now()
    message.save(update_fields=["text", "edited_at"])
    return message


def unsend_message(user, message):
    """Take back a message you sent.

    A soft delete that actually deletes the text. The row survives so the
    thread keeps its order and the other person sees "this message was
    unsent" rather than a conversation that quietly reads differently than
    they remember — but the words are gone from the database, because an
    unsent message the server still stores is not unsent.

    Idempotent, like every other write in this module: unsending twice is the
    same as unsending once, not an error.
    """
    if message.sender_id != user.pk:
        raise ValidationError("You can only unsend messages you sent.")
    if message.is_deleted:
        return message
    message.text = ""
    message.deleted_at = timezone.now()
    message.save(update_fields=["text", "deleted_at"])
    return message


# Temporary compatibility exports during domain extraction.
#
# Existing code still imports these symbols from palshare.services.
# Their implementations now live in their owning domain services.

from posts.services import (
    add_comment,
    attach_media,
)

from interactions.services import (
    reaction_summary,
    set_comment_like,
    set_like,
    set_reaction,
    set_save,
    set_share,
    toggle_comment_like,
    toggle_like,
    toggle_save,
    toggle_share,
)

# Temporary compatibility export during Connections extraction.
from connections.services import set_follow, toggle_follow
