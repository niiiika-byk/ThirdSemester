from django import forms
from .models import Registration,  Flight 
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
        labels = {
            'last_name': 'Фамилия',
            'first_name': 'Имя',
            'passport_series': 'Серия паспорта',
            'passport_number': 'Номер паспорта',
            'flight': 'Рейс',
        }
        
    def clean_passport_series(self):
        passport_series = self.cleaned_data.get('passport_series')
        if not passport_series.isdigit() or len(passport_series) != 4:
            raise forms.ValidationError("Серия паспорта должна состоять из 4 цифр.")
        return passport_series

    def clean_passport_number(self):
        passport_number = self.cleaned_data.get('passport_number')
        if not passport_number.isdigit() or len(passport_number) != 6:
            raise forms.ValidationError("Номер паспорта должен состоять из 6 цифр.")
        return passport_number