from accounts.serializers import PersonRowSerializer
from palshare.integrations import current_weather
from palshare.models import Reaction
from palshare.queries import suggestions_for


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
