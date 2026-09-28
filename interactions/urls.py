from django.urls import path

from . import views


app_name = "interactions"


urlpatterns = [
    path("posts/<int:pk>/like/", views.post_like, name="post-like"),
    path("posts/<int:pk>/save/", views.post_save, name="post-save"),
    path("posts/<int:pk>/share/", views.post_share, name="post-share"),
    path("posts/<int:pk>/react/", views.post_react, name="post-react"),
    path("comments/<int:pk>/like/", views.comment_like, name="comment-like"),
]
