import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

auth_logger = logging.getLogger('auth')

def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('login')
    else:   
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    # Получаем refresh токен из куков
    refresh_token = request.COOKIES.get('refresh_token')
    
    # Логируем выход пользователя
    auth_logger.info(
        f"User logout: user={request.user.username}, "
        f"refresh_token={'present' if refresh_token else 'missing'}"
    )
    
    # Делаем логаут Django
    logout(request)
    
    # Создаем ответ
    response = redirect('login')
    
    # Очищаем куки с токенами
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    
    return response

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                # Генерация JWT токенов
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                
                # Логируем успешный вход
                auth_logger.info(
                    f"User login successful: username={username}, "
                    f"user_id={user.id}, token_issued=True"
                )
                
                # Авторизация пользователя
                login(request, user)
                
                # Перенаправление с токенами
                response = redirect('home')
                response.set_cookie(
                    'access_token',
                    access_token,
                    httponly=True,
                    secure=True,
                    samesite='Lax',
                    max_age=3600  # 1 час
                )
                response.set_cookie(
                    'refresh_token',
                    str(refresh),
                    httponly=True,
                    secure=True,
                    samesite='Lax',
                    max_age=86400  # 1 день
                )
                return response
        else:
            # Логируем неудачную попытку входа
            auth_logger.warning(
                f"Failed login attempt: username={request.POST.get('username')}"
            )
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def refresh_token(request):
    refresh_token_value = request.COOKIES.get('refresh_token')
    
    if refresh_token_value:
        try:
            refresh = RefreshToken(refresh_token_value)
            new_access_token = str(refresh.access_token)
            
            # Логируем обновление токена
            auth_logger.info(
                f"Token refreshed: user={request.user.username}, "
                f"user_id={request.user.id}, "
                f"token_exp={refresh.payload['exp']}"
            )
            
            response = JsonResponse({'status': 'success'})
            response.set_cookie(
                'access_token',
                new_access_token,
                httponly=True,
                secure=True,
                samesite='Lax',
                max_age=3600
            )
            return response
        except Exception as e:
            # Логируем ошибку обновления токена
            auth_logger.error(
                f"Token refresh failed: user={request.user.username if request.user.is_authenticated else 'anonymous'}, "
                f"error={str(e)}"
            )
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    # Логируем отсутствие refresh токена
    auth_logger.warning(
        f"Refresh token missing: user={'anonymous' if not request.user.is_authenticated else request.user.username}"
    )
    return JsonResponse({'status': 'error', 'message': 'Refresh token missing'}, status=400)