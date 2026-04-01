from django.contrib import admin

from django.contrib import admin
from .models import MedicalRecord  # Agar tere table ka naam kuch aur hai toh wo likhna

# Ye line Django ko batati hai ki is table ko Admin panel mein dikhana hai
admin.site.register(MedicalRecord)
