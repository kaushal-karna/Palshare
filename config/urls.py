from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


urlpatterns = [
    # Django admin
    path("admin/", admin.site.urls),

    # Domain HTML urls
    path("", include("accounts.urls")),
    path("", include("posts.urls")),
    path("", include("connections.urls")),
    path("", include("interactions.urls")),
    path("", include("messaging.urls")),
    path("", include("search.urls")),
path("", include("integrations.urls")),

    # Legacy Palshare URL compatibility
    path(
    "palshare/",
    include(
        ("palshare.urls", "palshare_legacy"),
        namespace="palshare_legacy",
    ),
),

    # API
    path(
        "api/palshare/",
        include(("config.api_urls", "palshare-api"), namespace="palshare-api"),
    ),

    # OpenAPI schema
    path(
        "api/schema/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),

    # Swagger UI
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema",
        ),
        name="swagger-ui",
    ),

    # ReDoc
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(
            url_name="schema",
        ),
        name="redoc",
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )

