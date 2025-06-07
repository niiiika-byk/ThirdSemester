from django.shortcuts import render, redirect
from .forms import RegistrationForm, CreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required
from .models import Flight, Passenger, Registration
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from rest_framework_simplejwt.tokens import RefreshToken
import random, json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('register/login')

@login_required
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
    form = AuthenticationForm()  # Инициализируем форму для метода GET
    error = None  # Инициализируем переменную error
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user:
                login(request, user)
                
                # Генерация JWT
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                
                # Логируем токены
                logger.info(f"JWT generated for {user.username}:")
                logger.info(f"Access: {access_token[:50]}...")
                logger.info(f"Refresh: {str(refresh)[:50]}...")
                
                # Устанавливаем куки
                response = redirect('home')
                response.set_cookie(
                    'jwt_access_token',
                    access_token,
                    httponly=True,
                    secure=not settings.DEBUG,
                    samesite='Lax'
                )
                return response
            else:
                error = "Неверное имя пользователя или пароль."
        else:
            error = "Форма заполнена неверно."
    
    return render(request, 'login.html', {'form': form, 'error': error})

@login_required
def home_view(request):
    return render(request, 'home.html')

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
    page_number = request.GET.get('page')

    # Получаем базовый QuerySet с группировкой по рейсам
    registrations = Registration.objects.select_related('flight', 'passenger')
    
    if flight_id:
        registrations = registrations.filter(flight_id=flight_id)
    
    # Создаем словарь {рейс: [пассажиры]}
    flights_dict = {}
    for reg in registrations:
        flight = reg.flight
        if flight not in flights_dict:
            flights_dict[flight] = []
        flights_dict[flight].append({
            'first_name': reg.first_name,
            'last_name': reg.last_name,
            'suspicious_status': reg.passenger.suspicious_status if reg.passenger else 0,
            'registration_id': reg.id,
            'passenger_id': reg.passenger.id if reg.passenger else None
        })

    # Преобразуем в список для пагинации
    flights_list = list(flights_dict.items())
    
    # Пагинация по рейсам (не по пассажирам)
    paginator = Paginator(flights_list, 2)  # 2 рейса на страницу
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,  # Содержит (рейс, пассажиры) для текущей страницы
        'flights': flights,
        'selected_flight_id': flight_id,
    }
    return render(request, 'suspicious_passengers.html', context)

def logout_view(request):
    if hasattr(request, 'user') and request.user.is_authenticated:
        username = request.user.username
        logger.info(f"User {username} is logging out.")

        # Блокируем refresh токен
        try:
            refresh_token = RefreshToken.for_user(request.user)
            refresh_token.blacklist()
            logger.info(f"Refresh token blacklisted for user {username}.")
        except Exception as e:
            logger.error(f"Error blacklisting refresh token for user {username}: {e}")

    # Выход пользователя
    logout(request)

    # Создаем response для redirect
    response = redirect('login')
    
    # Очищаем JWT-токены из cookies
    response.delete_cookie('jwt_access_token')
    response.delete_cookie('jwt_refresh_token')
    logger.info(f"JWT tokens cleared from cookies for user {username}.")

    # Очищаем токены из сессии
    if 'jwt_access_token' in request.session:
        del request.session['jwt_access_token']
        logger.info(f"Access token cleared from session for user {username}.")
    if 'jwt_refresh_token' in request.session:
        del request.session['jwt_refresh_token']
        logger.info(f"Refresh token cleared from session for user {username}.")

    return response

@require_http_methods(["PUT"])
@login_required
def update_passenger_status(request, passenger_id):
    try:
        passenger = Passenger.objects.get(id=passenger_id)
        data = json.loads(request.body)
        passenger.suspicious_status = data.get('suspicious_status', 0)
        passenger.save()
        return JsonResponse({'status': 'success'})
    except Passenger.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Passenger not found'}, status=404)

@require_http_methods(["DELETE"])
@login_required
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