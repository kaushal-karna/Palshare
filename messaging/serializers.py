from django.template.defaultfilters import date as date_filter

from rest_framework import serializers

from messaging.models import Message

class MessageSerializer(serializers.ModelSerializer):
    """`mine` comes from the server, on purpose.

    `thread.html` says so in its own comment: working it out in the template by
    comparing usernames breaks the day somebody changes their display name.
    """

    mine = serializers.SerializerMethodField()
    sent_at = serializers.SerializerMethodField()
    # `deleted` and `edited` are booleans for the template, not timestamps:
    # the thread shows a state, not a date, and `{% if message.deleted %}`
    # reads better than a null check on a formatted string.
    deleted = serializers.BooleanField(source="is_deleted", read_only=True)
    edited = serializers.BooleanField(source="is_edited", read_only=True)

    class Meta:
        model = Message
        fields = ["id", "mine", "text", "sent_at", "deleted", "edited"]

    def get_mine(self, message) -> bool:
        request = self.context.get("request")
        return bool(request and message.sender_id == request.user.pk)

    def get_sent_at(self, message) -> str:
        return date_filter(message.sent_at, "H:i")
