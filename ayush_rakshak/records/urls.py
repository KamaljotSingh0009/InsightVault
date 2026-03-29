from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

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
    path('delete-report/<int:report_id>/', views.delete_report, name='delete_report'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)