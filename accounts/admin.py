from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Register your models here.

from .models import Profile, User



@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "is_staff",
        "is_verified",
        "is_private",
        "date_joined",
    )

    list_filter = (
        "is_staff",
        "is_verified",
        "is_private",
    )

    search_fields = (
        "username",
        "email",
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            "Palshare Account",
            {
                "fields": (
                    "is_verified",
                    "is_private",
                    "last_seen",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Palshare Account",
            {
                "fields": (
                    "email",
                    "is_verified",
                    "is_private",
                    "last_seen",
                )
            },
        ),
    )

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "location",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "location",
    )
