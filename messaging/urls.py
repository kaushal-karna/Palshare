"""Messaging HTML routes."""

from django.urls import path

from . import views


app_name = "messaging"


urlpatterns = [
    path(
        "u/<str:username>/message/",
        views.message_user,
        name="message-user",
    ),
    path(
        "inbox/",
        views.inbox,
        name="inbox",
    ),
    path(
        "inbox/<int:pk>/",
        views.thread,
        name="thread",
    ),
    path(
        "messages/<int:pk>/edit/",
        views.message_edit,
        name="message-edit",
    ),
    path(
        "messages/<int:pk>/unsend/",
        views.message_unsend,
        name="message-unsend",
    ),
]
