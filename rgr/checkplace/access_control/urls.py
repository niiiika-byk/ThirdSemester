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
    path('reports/', views.reports, name='reports'),
    path('verify-pass/', views.verify_pass, name='verify_pass'),
    path('request-pass/', views.request_pass, name='request_pass'),
]