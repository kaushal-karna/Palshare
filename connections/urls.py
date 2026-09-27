"""Connections HTML routes."""

from django.urls import path

from . import views

urlpatterns = [
    path(
        "u/<str:username>/connections/",
        views.connections,
        name="connections",
    ),
    path(
        "u/<str:username>/follow/",
        views.user_follow,
        name="user-follow",
    ),
]
