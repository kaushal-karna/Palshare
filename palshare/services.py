"""Shared business rules for Connections and Messaging.

Interaction state changes live in ``interactions.services``. This module
continues to provide the remaining connection and messaging service layer
during the domain extraction.
"""

from django.core.exceptions import ValidationError
from django.utils import timezone


from messaging.models import Conversation
from connections.models import Follow













# Temporary compatibility exports during domain extraction.
#
# Existing code still imports these symbols from palshare.services.
# Their implementations now live in their owning domain services.

from messaging.services import (
    conversation_with,
    edit_message,
    unsend_message,
)


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
