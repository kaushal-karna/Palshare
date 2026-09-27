"""The JSON half of the app. The other half is `views.py`.

Both import `visible_posts` from `queries.py`, so the rule about who may see
what is written once and applied twice. That is the whole point of Part 4.
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from posts.models import Post
from .permissions import IsAuthorOrReadOnly
from .queries import people, visible_posts
from accounts.serializers import PersonSerializer
from .serializers import PostSerializer
from .services import (reaction_summary, set_follow, set_like, set_reaction,
                       set_save, set_share)

User = get_user_model()



class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.none()  # see PostViewSet
    serializer_class = PersonSerializer
    permission_classes = [IsAuthenticated]
    # A profile URL says `/u/kaushal/`, not `/u/7/`.
    lookup_field = "username"

    def get_queryset(self):
        return people(self.request.user, User.objects.select_related("profile"))

    @action(detail=True, methods=["post"])
    def follow(self, request, username=None):
        try:
            set_follow(request.user, self.get_object(), True)
        except ValueError as error:
            # The CheckConstraint would also stop this, with a 500. A 400 with
            # a sentence is the version a person can act on.
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"following": True})

    @action(detail=True, methods=["post"])
    def unfollow(self, request, username=None):
        set_follow(request.user, self.get_object(), False)
        return Response({"following": False})

# Temporary compatibility import during domain extraction.
from posts.api import PostViewSet
