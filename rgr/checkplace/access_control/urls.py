from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_login, name='login'),
    path('home/', views.home, name='home'), 
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/refresh-token/', views.refresh_token, name='refresh_token'),
    path('review-request/<int:request_id>/', views.review_request, name='review_request'),
    path('check_access/', views.check_access, name='check_access'),
    path('request-pass/', views.request_pass, name='request_pass'),
]