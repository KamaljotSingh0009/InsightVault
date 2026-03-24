from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_user, name='login'), 
    path('profile/', views.profile, name='profile'),
    path('register/step1/', views.register_step1, name='register_step1'), # NAYA
    path('register/step2/', views.register_step2, name='register_step2'), # NAYA
    path('logout/', views.logout_user, name='logout'),
    path('upload/', views.upload_report, name='upload_report'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('vault/', views.my_vault, name='vault'),
    
]