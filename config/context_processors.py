from accounts.serializers import PersonRowSerializer
from integrations.services import current_weather
from interactions.models import Reaction
from connections.queries import suggestions_for


def common_ui(request):
    if not request.user.is_authenticated:
        return {}

    user = request.user

    return {
        "current_user": PersonRowSerializer(
            user,
            context={"request": request},
        ).data,
        "weather": current_weather(),
        "emoji": [
            value
            for value, _ in Reaction.EMOJI
        ],
        "suggestions": PersonRowSerializer(
            suggestions_for(user),
            many=True,
            context={"request": request},
        ).data,
    }
