from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_user, name='login'), 
    path('register/step1/', views.register_step1, name='register_step1'), # NAYA
    path('register/step2/', views.register_step2, name='register_step2'), # NAYA
    path('logout/', views.logout_user, name='logout'),
    path('upload/', views.upload_report, name='upload_report'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('vault/', views.my_vault, name='vault'),
    path('delete-report/<int:report_id>/', views.delete_report, name='delete_report'),
    path('risk-analysis/', views.risk_analysis, name='risk_analysis'),
    path('diet-plan/', views.smart_diet, name='smart_diet'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('save-habits/', views.save_habits, name='save_habits'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('patient/<int:patient_id>/file/', views.patient_file, name='patient_file'),
    path('my-prescriptions/', views.my_prescriptions, name='my_prescriptions'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)