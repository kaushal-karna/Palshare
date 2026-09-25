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

    # Accounts urls live
    path("", include("accounts.urls")),
    # Main Palshare application
    path("", include("palshare.urls")),
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
        include("palshare.api_urls"),
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
