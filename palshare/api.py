"""Compatibility facade for the extracted API domains."""

from connections.api import UserViewSet
from posts.api import PostViewSet


__all__ = ["PostViewSet", "UserViewSet"]
