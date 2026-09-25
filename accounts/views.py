from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import login


from django.shortcuts import redirect, render

from .forms import RegistrationForm

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
