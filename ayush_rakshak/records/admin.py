from django.contrib import admin
from .models import Prescription, UserProfile, MedicalRecord, DietHabit

class UserProfileAdmin(admin.ModelAdmin):
    # Ye columns exactly Excel sheet ki tarah dikhenge
    list_display = ('patient_id', 'user', 'assigned_doctor', 'age', 'phone')
    
    # Ye Admin panel mein upar ek Search Bar laga dega!
    search_fields = ('patient_id', 'user__username', 'user__email', 'phone')
    
    # Ye right side mein ek Filter laga dega (Doctor ke hisaab se patients filter karne ke liye)
    list_filter = ('assigned_doctor',)

# Tables ko Admin Panel mein Register kar rahe hain
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(MedicalRecord)
admin.site.register(DietHabit)
admin.site.register(Prescription)
