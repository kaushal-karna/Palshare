"""Compatibility URL facade.

Canonical route ownership lives in the domain applications.
This module only preserves the legacy ``palshare:`` namespace while
existing templates/tests are migrated.
"""

from django.urls import path

from accounts.views import user_profile
from interactions.urls import urlpatterns as interactions_urlpatterns
from connections.urls import urlpatterns as connections_urlpatterns
from messaging.urls import urlpatterns as messaging_urlpatterns
from posts.urls import urlpatterns as posts_urlpatterns
from search.urls import urlpatterns as search_urlpatterns


app_name = "palshare"


urlpatterns = (
    posts_urlpatterns
    + connections_urlpatterns
    + interactions_urlpatterns
    + messaging_urlpatterns
    + search_urlpatterns
    + [
        path(
            "u/<str:username>/",
            user_profile,
            name="profile",
        ),
    ]
)
