from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import UserLoginView, profile_view, register_view, profile_edit, settings_view, user_profile


app_name = "accounts"


urlpatterns = [
    # Auth
    path(
        "register/",
        register_view,
        name="register",
    ),

    path(
        "login/",
        UserLoginView.as_view(),
        name="login",
    ),

    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),

    path(
        "profile/",
        profile_view,
        name="profile",
    ),

    path("u/<str:username>/", user_profile, name="user-profile"),

    path(
    "u/<str:username>/edit/",
    profile_edit,
    name="profile-edit",
),

    # Settings (public / private profile lives here)
path(
    "settings/",
    settings_view,
    name="settings",
),
]
