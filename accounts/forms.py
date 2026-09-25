from django import forms
from django.contrib.auth.password_validation import validate_password

from .models import User


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
            }
        ),
        required=True,
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
        )

    def clean_username(self):
        username = self.cleaned_data.get("username")

        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("That username is taken")

        return username

    def clean_password(self):
        password = self.cleaned_data.get("password")
        validate_password(password)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user


class ProfileEditForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        required=False,
    )
    bio = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea,
    )
    avatar = forms.ImageField(
        required=False,
    )


class PrivacySettingsForm(forms.Form):
    is_private = forms.BooleanField(
        required=False,
    )
