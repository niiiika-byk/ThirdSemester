from django.urls import path
from .views import registration_view, home_view, login_view, register, logout_view, suspicious_passengers
from .views import update_passenger_status, delete_registration

handler403 = 'flight.views.handler403'
handler401 = 'flight.views.handler401'

urlpatterns = [
    path('registration/', registration_view, name='registration'),
    path('', login_view, name='login_view'),
    path('home/', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('register/', register, name='register'),
    path('logout/', logout_view, name='logout'),
    path('suspicious-passengers/', suspicious_passengers, name='suspicious_passengers'),
    path('api/passengers/<int:passenger_id>/status/', update_passenger_status, name='update_passenger_status'),
    path('api/registrations/<int:registration_id>/', delete_registration, name='delete_registration'),
]