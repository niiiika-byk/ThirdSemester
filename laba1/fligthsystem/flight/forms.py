from django import forms
from .models import Registration

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ['last_name', 'first_name', 'passport_series', 'passport_number', 'flight']