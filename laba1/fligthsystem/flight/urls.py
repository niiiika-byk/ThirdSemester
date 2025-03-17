from django.urls import path
from .views import registration_view, home_view, login_view, register

urlpatterns = [
    path('registration/', registration_view, name='registration'),
    path('', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('register/', register, name='register'),
]