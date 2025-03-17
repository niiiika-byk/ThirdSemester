from django.shortcuts import render, redirect
from .forms import RegistrationForm, CreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse_lazy
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required
from .models import Flight, Passenger
import random

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('register/login')

def register(request):
    if request.method == 'POST':
        form = CreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Перенаправление на страницу входа
    else:
        form = CreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')  # Перенаправление на домашнюю страницу после входа
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def home_view(request):
    return render(request, 'home.html')

import random

@login_required
def registration_view(request):
    success_message = None
    flights = Flight.objects.all()  # Получаем все рейсы

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Сохраняем данные формы
            registration = form.save(commit=False)  # Не сохраняем еще в БД

            # Создаем экземпляр Passenger с рандомным статусом
            passenger = Passenger()

            # Генерируем статус с меньшей вероятностью для "Подозрительный"
            if random.random() < 0.2:  # 20% вероятность быть подозрительным
                passenger.suspicious_status = 1
            else:
                passenger.suspicious_status = 0

            passenger.save()  # Сохраняем пассажира в базе данных

            # Связываем регистрацию с пассажиром
            registration.passenger = passenger
            registration.save()  # Сохраняем регистрацию в базе данных

            success_message = "Регистрация прошла успешно!"
            if passenger.suspicious_status == 1:
                success_message += " Статус: Подозрительный."

    else:
        form = RegistrationForm()

    return render(request, 'registration.html', {
        'form': form,
        'success_message': success_message,
        'flights': flights
    })

@login_required
def suspicious_passengers(request):
    flights = Flight.objects.all()  # Получаем все рейсы

    if request.user.is_staff:
        # Получаем ID рейса из GET-запроса, если он есть
        flight_id = request.GET.get('flight_id')

        if flight_id:
            # Фильтруем пассажиров по выбранному рейсу
            suspicious_passengers = Passenger.objects.filter(suspicious_status=1, registration__flight=flight_id).prefetch_related('registration_set')
        else:
            # Если рейс не выбран, получаем всех подозрительных пассажиров
            suspicious_passengers = Passenger.objects.filter(suspicious_status=1).prefetch_related('registration_set')

        return render(request, 'suspicious_passengers.html', context={
            'suspicious_passengers': suspicious_passengers,
            'flights': flights  # Передаем рейсы в контекст
        })

    # Если не администратор, можно вернуть пустой список или сообщение
    return render(request, 'suspicious_passengers.html', context={'suspicious_passengers': [], 'flights': flights})

def logout_view(request):
    logout(request)
    return redirect('login')