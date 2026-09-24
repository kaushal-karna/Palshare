from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.defaultfilters import date as date_filter
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer


User = get_user_model()


def initial(user):
    """The one-letter avatar every card and row renders.

    A letter, not an <img>: uploads are Part 6, and a layout that only looks
    right once media exists is a layout nobody can review in hour one.
    """
    return (user.get_full_name() or user.username or "?")[:1].upper()


def display_name(user):
    """`get_full_name()` alone renders an empty byline for anyone who signed up
    without a first name — which is everybody, at a workshop."""
    return user.get_full_name() or user.username


# `blog` already registers a component called "Author". Two different shapes
# under one name is a schema that lies about one of them.
@extend_schema_serializer(component_name="PalShareAuthor")
class AuthorSerializer(serializers.ModelSerializer):
    """A user as a byline: the fields a post card actually shows.

    Deliberately smaller than PersonSerializer. Nesting the big one inside a
    post costs two extra queries per row for follower counts nobody is looking
    at — twenty of them on a ten-post page.
    """

    name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    # The letter stays. `avatar_url` is the picture when there is one, and the
    # templates fall back to the letter when there is not — which is most
    # people, most of the time, and is a state the shell was designed around.
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "name", "avatar", "avatar_url"]

    def get_name(self, user) -> str:
        return display_name(user)

    def get_avatar(self, user) -> str:
        return initial(user)

    def get_avatar_url(self, user) -> str:
        """None-safe three times over: no Profile row, no file, no MEDIA_URL.

        `user.profile` raises for anyone whose row was created outside this app
        — the admin, `createsuperuser`, a fixture — and that is most of the
        users in a workshop database.
        """
        profile = getattr(user, "profile", None)
        avatar = getattr(profile, "avatar", None)
        if not avatar:
            return ""
        request = self.context.get("request")
        return request.build_absolute_uri(avatar.url) if request else avatar.url


# The component name is inherited along with everything else, so each subclass
# has to claim its own or they all register as "PalShareAuthor".
@extend_schema_serializer(component_name="PalSharePersonRow")
class PersonRowSerializer(AuthorSerializer):
    """One person in a list: search results, followers, following, suggestions.

    `is_following` is read off the annotation `queries.people()` adds, not
    computed here — a `SerializerMethodField` that queries is one query per
    row, and these are all rows.
    """

    bio = serializers.CharField(source="profile.bio", read_only=True, default="")
    is_following = serializers.BooleanField(read_only=True, default=False)

    class Meta(AuthorSerializer.Meta):
        fields = AuthorSerializer.Meta.fields + ["bio", "is_following"]


@extend_schema_serializer(component_name="PalSharePerson")
class PersonSerializer(PersonRowSerializer):
    """The profile header, where the follower counts are actually on screen.

    Two `.count()` calls per person — which is why this one stays on the
    profile page and `PersonRowSerializer` is what lists use.
    """

    followers = serializers.IntegerField(source="followers.count", read_only=True)
    following = serializers.IntegerField(source="following.count", read_only=True)
    post_count = serializers.IntegerField(source="posts.count", read_only=True)
    is_private = serializers.BooleanField(read_only=True, default=False)
    is_me = serializers.SerializerMethodField()
    joined = serializers.SerializerMethodField()

    class Meta(PersonRowSerializer.Meta):
        fields = PersonRowSerializer.Meta.fields + [
            "followers", "following", "post_count", "is_private", "is_me", "joined",
        ]

    def get_is_me(self, user) -> bool:
        request = self.context.get("request")
        return bool(request and request.user.pk == user.pk)

    def get_joined(self, user) -> str:
        return date_filter(user.date_joined, "F Y")

