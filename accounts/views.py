from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView

from django.shortcuts import redirect, render

from .forms import RegistrationForm

# Create your views here.

def register_view(request):
    if request.user.is_authenticated:
        return redirect("profile")
    
    if request.method=="POST":
        form = RegistrationForm(request.POST)
        
        if form.is_valid():
            form.save()
            return redirect("login")
        
    else:
        form = RegistrationForm()
        
    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )
    

def UserLoginView(LoginView):
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