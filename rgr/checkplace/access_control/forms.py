from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone', 'role', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Русские labels
        self.fields['username'].label = 'Логин'
        self.fields['email'].label = 'Электронная почта'
        self.fields['phone'].label = 'Телефон'
        self.fields['role'].label = 'Роль'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтверждение пароля'
        
        # Русские help_texts
        self.fields['username'].help_text = 'Только буквы, цифры и @/./+/-/_'
        self.fields['password1'].help_text = '''
            <ul class="password-help">
                <li>Пароль не должен быть слишком похож на другую личную информацию</li>
                <li>Пароль должен содержать как минимум 8 символов</li>
                <li>Пароль не должен быть слишком простым</li>
                <li>Пароль не может состоять только из цифр</li>
            </ul>
        '''