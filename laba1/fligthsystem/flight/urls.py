from django.urls import path
from .views import registration_view, home_view

urlpatterns = [
    path('registration/', registration_view, name='registration'),
    path('', home_view, name='home'),
]