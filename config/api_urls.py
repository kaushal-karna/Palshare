"""Project-level API routing.

Domain ViewSets remain owned by their respective applications.
This module only composes the public API surface.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from connections.api import UserViewSet
from posts.api import PostViewSet


app_name = "palshare-api"

router = DefaultRouter()
router.register("posts", PostViewSet, basename="post")
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
]
