# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CustomUserCreationForm(UserCreationForm):
    """Extended signup form with email, first name, and last name"""

    first_name = forms.CharField(
        max_length=30,
        required=True,
        help_text='Enter your first name.'
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        help_text='Enter your last name.'
    )
    email = forms.EmailField(
        required=True,
        help_text='Required. This will also be your username.'
    )

    class Meta:
        model = User
        fields = ('email', 'first_name',
                  'last_name', 'username', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')

        # Check if email is already in use
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        # Ensure email is set and validated
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']  # ← Add this
        user.last_name = self.cleaned_data['last_name']    # ← Add this
        # Set username to the provided value
        # user.username = self.cleaned_data['username'] Django's UserCreationForm already handles username, so we don't need to set it here
        if commit:
            user.save()
        return user
