"""Connections HTML views."""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.serializers import PersonRowSerializer
from accounts.models import User
from connections.queries import people
from connections.services import toggle_follow
from palshare.view_helpers import back, shell, signed_in


@signed_in
def connections(request, username):
    owner = get_object_or_404(User, username=username)
    tab = request.GET.get("tab", "followers")
    # `owner.followers` is the Follow rows where owner is followed, so the
    # people are on the other end of each row. Read the related_names in
    # models.py before changing this line; they are the opposite of what they
    # look like.
    if tab == "following":
        queryset = User.objects.filter(followers__follower=owner)
    else:
        queryset = User.objects.filter(following__following=owner)
    return render(request, "palshare/connections.html", shell(
        request,
        people=PersonRowSerializer(people(request.user, queryset), many=True,
                                context={"request": request}).data,
    ))


@signed_in
@require_POST
def user_follow(request, username):
    target = get_object_or_404(User, username=username)
    try:
        toggle_follow(request.user, target)
    except ValueError as error:
        messages.error(request, str(error))
    return back(request, reverse("palshare:profile", args=[target.username]))
