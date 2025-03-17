from django.urls import path
from .views import registration_view, home_view, login_view, register, logout_view, suspicious_passengers

urlpatterns = [
    path('registration/', registration_view, name='registration'),
    path('', login_view, name='login_view'),
    path('home/', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('register/', register, name='register'),
    path('logout/', logout_view, name='logout'),
    path('suspicious-passengers/', suspicious_passengers, name='suspicious_passengers'),
]