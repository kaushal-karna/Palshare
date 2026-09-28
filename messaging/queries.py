from messaging.models import Conversation

def conversations_for(me):
    """Every conversation `me` is in, newest first, with the two facts the
    inbox badge needs: the other participant and how many unread messages.

    `prefetch_related` then counting in Python, rather than a `.filter()` per
    row: the prefetch is two queries for the whole page, and re-filtering a
    prefetched relation throws the cache away and goes back to the database.
    """
    rows = []
    for conversation in (Conversation.objects
                         .filter(participants=me)
                         .prefetch_related("participants", "messages__sender")):
        others = [p for p in conversation.participants.all() if p.pk != me.pk]
        messages = list(conversation.messages.all())
        rows.append({
            "conversation": conversation,
            "other": others[0] if others else me,
            "last": messages[-1] if messages else None,
            "unread": sum(1 for m in messages
                          if m.read_at is None and m.sender_id != me.pk),
        })
    return rows
