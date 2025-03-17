from django import forms
from .models import Registration
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User  = get_user_model()

class CreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Этот адрес электронной почты уже занят.")
        return email

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ['last_name', 'first_name', 'passport_series', 'passport_number', 'flight']