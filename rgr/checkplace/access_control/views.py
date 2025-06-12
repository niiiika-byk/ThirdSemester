import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
from .models import AirportPass, PassRequest, AccessZone, CustomUser
from django.contrib.auth.decorators import login_required
from datetime import date
from django.contrib import messages

auth_logger = logging.getLogger('auth')

@login_required
def home(request):
    context = {
        'current_date': date.today().isoformat()
    }
    
    if request.user.role == 'ADMIN':
        context['active_passes_count'] = AirportPass.objects.filter(is_active=True).count()
        context['pending_requests_count'] = PassRequest.objects.filter(status='PENDING').count()

        context['recent_requests'] = PassRequest.objects.select_related('user').order_by('-created_at')[:5]
        
    elif request.user.role == 'SECURITY':
        context['active_passes'] = AirportPass.objects.filter(is_active=True).select_related('owner')[:20]
        
    elif request.user.role == 'STAFF':
        # Активный пропуск (последний одобренный)
        context['active_pass'] = AirportPass.objects.filter(
            owner=request.user,
            is_active=True
        ).order_by('-expiry_date').first()
        
        # Все запросы пропусков пользователя
        context['pass_requests'] = PassRequest.objects.filter(
            user=request.user
        ).order_by('-created_at')
    
    return render(request, 'home.html', context)

@login_required
def request_pass(request):
    if request.method == 'POST':
        if request.user.role != 'STAFF':
            messages.error(request, 'Только сотрудники могут запрашивать пропуски')
            return redirect('home')
            
        access_zone = request.POST.get('access_zone')
        purpose = request.POST.get('purpose')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        if all([access_zone, purpose, start_date, end_date]):
            try:
                PassRequest.objects.create(
                    user=request.user,
                    access_zone=access_zone,
                    purpose=purpose,
                    start_date=start_date,
                    end_date=end_date
                )
                messages.success(request, 'Ваш запрос отправлен на рассмотрение')
            except Exception as e:
                messages.error(request, f'Ошибка при создании заявки: {e}')
        else:
            messages.error(request, 'Заполните все поля')
    
    return redirect('home')

@login_required
def review_request(request, request_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Доступ запрещен')
        return redirect('home')
    
    try:
        pass_request = PassRequest.objects.get(id=request_id)
    except PassRequest.DoesNotExist:
        messages.error(request, 'Заявка не найдена')
        return redirect('home')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        reason = request.POST.get('reason', '')
        
        if action == 'approve':
            try:
                AirportPass.objects.create(
                    owner=pass_request.user,
                    access_zone=pass_request.access_zone,
                    issue_date=pass_request.start_date,
                    expiry_date=pass_request.end_date,
                    is_active=True
                )
                pass_request.status = 'APPROVED'
                pass_request.save()
                messages.success(request, 'Заявка одобрена')
            except Exception as e:
                messages.error(request, f'Ошибка при создании пропуска: {e}')
            
        elif action == 'reject':
            pass_request.status = 'REJECTED'
            pass_request.rejection_reason = reason
            pass_request.save()
            messages.success(request, 'Заявка отклонена')
    
    return redirect('home')

@login_required
def check_access(request):
    if request.user.role != 'SECURITY':
        messages.error(request, 'Доступ запрещен: только для службы безопасности')
        return redirect('home')
    
    zones = AccessZone.objects.all()
    
    # Исправленный запрос для получения персонала с активными пропусками
    staff_users = CustomUser.objects.filter(
        role='STAFF'
    ).prefetch_related('airportpass_set').filter(
        airportpass__is_active=True
    ).distinct()
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        zone_id = request.POST.get('zone_id')
        
        try:
            zone = AccessZone.objects.get(id=zone_id)
            user = CustomUser.objects.get(id=user_id)
            user_pass = user.airportpass_set.filter(is_active=True).first()
            
            if not user_pass:
                message = "У сотрудника нет активного пропуска"
                access_granted = False
            elif user_pass.has_access_to(zone.zone_type):
                message = f"Доступ в {zone.name} разрешен"
                access_granted = True
            else:
                message = f"Недостаточный уровень доступа (Требуется: {zone.get_required_access_level_display()})"
                access_granted = False
                
            return JsonResponse({
                'status': 'access_granted' if access_granted else 'access_denied',
                'message': message,
                'required_level': zone.get_required_access_level_display(),
                'user_level': user_pass.get_access_level_display() if user_pass else 'Нет пропуска'
            })
            
        except (AccessZone.DoesNotExist, CustomUser.DoesNotExist) as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Ошибка: неверные данные'
            }, status=400)

    return render(request, 'security_dashboard.html', {
        'zones': zones,
        'staff_users': staff_users,
    })

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