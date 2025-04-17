from django.shortcuts import render, redirect
from .forms import RegistrationForm, CreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse_lazy
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required
from .models import Flight, Passenger, Registration
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import random, json

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
            registration = form.save(commit=False)

            passenger = Passenger()

            if random.random() < 0.2:
                passenger.suspicious_status = 1
            else:
                passenger.suspicious_status = 0

            passenger.save()

            registration.passenger = passenger
            registration.save()

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
    flights = Flight.objects.all()
    flight_id = request.GET.get('flight_id')

    registrations = Registration.objects.select_related('flight', 'passenger').all()

    passengers_by_flight = {}

    for registration in registrations:
        flight_number = registration.flight.flight_number
        suspicious_status = registration.passenger.suspicious_status if registration.passenger else 0

        passenger_data = {
            'first_name': registration.first_name,
            'last_name': registration.last_name,
            'suspicious_status': suspicious_status,
            'registration_id': registration.passenger_id,
            'passenger_id': registration.passenger.id if registration.passenger else None
        }

        if flight_id is None or str(registration.flight.id) == flight_id:
            if flight_number not in passengers_by_flight:
                passengers_by_flight[flight_number] = []
            passengers_by_flight[flight_number].append(passenger_data)

    context = {
        'passengers_by_flight': passengers_by_flight,
        'flights': flights,
        'selected_flight_id': flight_id,
    }
    return render(request, 'suspicious_passengers.html', context)

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
@require_http_methods(["PUT"])
def update_passenger_status(request, passenger_id):
    try:
        passenger = Passenger.objects.get(id=passenger_id)
        data = json.loads(request.body)
        passenger.suspicious_status = data.get('suspicious_status', 0)
        passenger.save()
        return JsonResponse({'status': 'success'})
    except Passenger.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Passenger not found'}, status=404)

@login_required
@require_http_methods(["DELETE"])
def delete_registration(request, registration_id):
    try:
        data = json.loads(request.body)
        passenger_id = data.get('passenger_id')

        if passenger_id:
            Passenger.objects.filter(id=passenger_id).delete()

        registration = Registration.objects.get(id=registration_id)
        registration.delete()
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)