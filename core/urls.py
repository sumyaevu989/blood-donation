from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('request-blood/', views.request_blood_view, name='request_blood'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('camps/', views.camps, name='camps'),
    path('join-camp/<int:camp_id>/', views.join_camp, name='join_camp'),
    path('verify-request/<int:req_id>/', views.verify_otp, name='verify_otp'),
    path('certificate/', views.generate_certificate, name='generate_certificate'),
]