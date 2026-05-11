from django.db import models
from django.contrib.auth.models import User
import random
import string
class UserProfile(models.Model):
    # Ye line UserProfile ko default User se jodti hai (Patient khud)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    #  Multi-Tenant Connection - Har Patient ka ek assigned Doctor hoga, aur Doctor ke paas multiple Patients ho sakte hain.
    # limit_choices_to={'is_staff': True} ensures ki dropdown mein sirf Admins (Doctors) ka naam aaye, dusre patients ka nahi!
    assigned_doctor = models.ForeignKey(
        User, 
        related_name='my_patients', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        limit_choices_to={'is_staff': True} 
    )
    patient_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    age = models.IntegerField(null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)

    # Auto Generate ID before saving
    def save(self, *args, **kwargs):
        if not self.patient_id:
            random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            self.patient_id = f"PT-{random_string}"
        super().save(*args, **kwargs)

    # The Ultimate String Representation for Admin Panel
    def __str__(self):
        doctor_name = self.assigned_doctor.username if self.assigned_doctor else 'Unassigned'
        p_id = self.patient_id if self.patient_id else 'NO-ID'
        return f"{self.user.username} | {p_id} | Dr: {doctor_name}"
class MedicalRecord(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE)
    report_image = models.FileField(upload_to='patient_reports/')
    extracted_data = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    ANALYSIS_STATUS = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=ANALYSIS_STATUS, default='pending')

    def __str__(self):
        return f"Report of {self.patient.username} on {self.uploaded_at.strftime('%Y-%m-%d')}"




class DietHabit(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    habit_json = models.TextField(default="[]")

    last_updated = models.DateTimeField(auto_now=True, null=True)
    #Added for clean Admin Panel view
    def __str__(self):
        return f"{self.user.username}'s Diet Habits"
    


class Prescription(models.Model):
    # 'on_delete=models.CASCADE' -> Agar patient apna account delete karega, tabhi uski history ud jayegi.
    patient = models.ForeignKey(User, related_name='prescriptions', on_delete=models.CASCADE)
    
    # 'on_delete=models.SET_NULL' -> Ye hai magic! Agar patient apna Clinic badal le, 
    # ya original Doctor apna account delete bhi kar de, toh bhi patient ki purani parchi safe rahegi.
    doctor = models.ForeignKey(User, related_name='issued_prescriptions', on_delete=models.SET_NULL, null=True, limit_choices_to={'is_staff': True})
    
    # MVP Medical Fields (Simple & Flexible)
    diagnosis_or_symptoms = models.CharField(max_length=255, blank=True, null=True) # Optional: Ongoing bimari ke liye
    medicines = models.TextField() # Required: Doctor dawaiyan yahan type karega
    notes = models.TextField(blank=True, null=True) # Optional: "Subah sham khana" etc.
    
    # Auto Timestamp (Doctor ko date dalne ki zaroorat nahi)
    created_at = models.DateTimeField(auto_now_add=True)

    # Admin Panel mein sundar dikhne ke liye
    def __str__(self):
        doctor_name = self.doctor.username if self.doctor else 'Unknown'
        return f"Rx: {self.patient.username} | {self.created_at.strftime('%d-%m-%Y')} | Dr. {doctor_name}"