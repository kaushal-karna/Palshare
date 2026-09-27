"""Compatibility facade for Post API permissions."""

from posts.permissions import IsAuthorOrReadOnly

__all__ = ["IsAuthorOrReadOnly"]
