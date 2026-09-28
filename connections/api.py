"""API endpoints for people and follow-graph operations."""

from django.contrib.auth import get_user_model

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.serializers import PersonSerializer
from connections.queries import people
from connections.services import set_follow


User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.none()
    serializer_class = PersonSerializer
    permission_classes = [IsAuthenticated]

    # A profile URL says /u/kaushal/, not /u/7/.
    lookup_field = "username"

    def get_queryset(self):
        return people(
            self.request.user,
            User.objects.select_related("profile"),
        )

    @action(detail=True, methods=["post"])
    def follow(self, request, username=None):
        try:
            set_follow(request.user, self.get_object(), True)
        except ValueError as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"following": True})

    @action(detail=True, methods=["post"])
    def unfollow(self, request, username=None):
        set_follow(request.user, self.get_object(), False)
        return Response({"following": False})
