from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

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
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def refresh_token(request):
    refresh_token = request.COOKIES.get('refresh_token')
    
    if refresh_token:
        try:
            refresh = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)
            
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
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Refresh token missing'}, status=400)