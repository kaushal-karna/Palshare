from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import login, logout as auth_logout
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.http import HttpResponseForbidden


from .models import Profile
from .serializers import PersonSerializer
from .forms import RegistrationForm, PrivacySettingsForm, ProfileEditForm
from .services import update_privacy, update_profile




# Create your views here.

# --- auth -----------------------------------------------------------------

def register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:profile")

    if request.method=="POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user=form.save()
            login(request, user)
            return redirect("palshare:feed")

    else:
        form = RegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


@login_required
def profile_view(request):
    profile = request.user.profile

    return render(
        request,
        "accounts/profile.html",
        {
            "profile": profile,
        },
    )



@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def profile_edit(request, username):
    if username != request.user.username:
        return HttpResponseForbidden(
            "You can only edit your own profile."
        )

    profile = Profile.objects.get_or_create(
        user=request.user
    )[0]

    if request.method == "POST":
        form = ProfileEditForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                update_profile(
                    request.user,
                    profile,
                    name=form.cleaned_data["name"],
                    bio=form.cleaned_data["bio"],
                    avatar=form.cleaned_data.get("avatar"),
                )
            except ValidationError as exc:
                for message in exc.messages:
                    messages.error(request, message)

                return render(
                    request,
                    "accounts/profile_edit.html",
                    {
                        "profile": PersonSerializer(
                            request.user,
                            context={"request": request},
                        ).data,
                        "form": form,
                    },
                )

            messages.success(
                request,
                "Profile updated.",
            )

            return redirect(
                ("accounts:profile"),
                # username=request.user.username,
            )


    else:
        profile_data = PersonSerializer(
            request.user,
            context={"request": request},
        ).data

        form = ProfileEditForm(
            initial={
                "name": (
                    f"{request.user.first_name} "
                    f"{request.user.last_name}"
                ).strip(),
                "bio": profile.bio,
            }
        )

    upload = request.FILES.get("avatar")

    return render(
        request,
        "accounts/profile_edit.html",
        {
            "profile": profile_data
            if request.method == "GET"
            else PersonSerializer(
                request.user,
                context={"request": request},
            ).data,
            "form": form,
            "upload_name": upload.name if upload else "",
        },
    )



# --- settings -------------------------------------------------------------

@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def settings_view(request):
    if request.method == "POST":
        form = PrivacySettingsForm(request.POST)

        if form.is_valid():
            if "logout" in request.POST:
                auth_logout(request)
                return redirect("accounts:login")

            update_privacy(
                request.user,
                form.cleaned_data["is_private"],
            )

            messages.success(
                request,
                "Settings saved.",
            )

            return redirect(
                "accounts:settings"
            )
    else:
        form = PrivacySettingsForm(
            initial={
                "is_private": request.user.is_private,
            }
        )

    return render(
        request,
        "accounts/settings.html",
        {
            "form": form,
            "profile": PersonSerializer(
                request.user,
                context={"request": request},
            ).data,
        },
    )
