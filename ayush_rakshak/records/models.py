from django.db import models
from django.contrib.auth.models import User

# Nayi Table: Custom user details ke liye
class UserProfile(models.Model):
    # Ye line UserProfile ko default User se jodti hai (One-to-One Link)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField(null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return self.user.username

# Puraana MedicalRecord wala code yahan waisa hi rahega...
class MedicalRecord(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE)
    report_image = models.ImageField(upload_to='patient_reports/')
    extracted_data = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report of {self.patient.username} on {self.uploaded_at.strftime('%Y-%m-%d')}"