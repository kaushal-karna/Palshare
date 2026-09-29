"""Posts HTML routes."""

from django.urls import path

from . import views


app_name = "posts"

urlpatterns = [
    # Feed and posts
    path("", views.feed, name="feed"),
    path("posts/new/", views.post_create, name="post-create"),
    path("posts/<int:pk>/", views.post_detail, name="post-detail"),
    path("posts/<int:pk>/edit/", views.post_edit, name="post-edit"),
    path("saved/", views.saved, name="saved"),
]
