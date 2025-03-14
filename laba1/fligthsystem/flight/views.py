from django.shortcuts import render, redirect
from .forms import RegistrationForm

def registration_view(request):
    success_message = None
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            success_message = "Регистрация прошла успешно!"
    else:
        form = RegistrationForm()
    return render(request, 'registration.html', {'form': form, 'success_message': success_message})