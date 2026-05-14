import os
import re 
import json
import time 
from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from httpx import request
from django.http import JsonResponse
from .models import DietHabit, UserProfile, Prescription, MedicalRecord
from .ml_predict import get_heart_risk, get_diabetes_risk
from django.contrib import messages
from google import genai
from dotenv import load_dotenv
import PIL.Image
from django.db.models import Q
from django.core.paginator import Paginator
import fitz # PyMuPDF
import io

load_dotenv()


# STEP 1: Basic Info
def register_step1(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        # Prevent duplicate registration at the first step
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already registered. Please login instead.')
            return redirect('login')
        
        # Store valid user data in session for step 2
        request.session['reg_first'] = request.POST.get('first_name')
        request.session['reg_last'] = request.POST.get('last_name')
        request.session['reg_age'] = request.POST.get('age')
        request.session['reg_nationality'] = request.POST.get('nationality')
        request.session['reg_email'] = request.POST.get('email')
        request.session['reg_phone'] = request.POST.get('phone')
        request.session['reg_doctor_id'] = request.POST.get('assigned_doctor')
        return redirect('register_step2')
    
    doctors = User.objects.filter(is_staff=True)
    return render(request, 'records/register_step1.html', {'doctors': doctors})

# STEP 2: Password & Final Account Creation
def register_step2(request):
    if request.method == 'POST':
        p1 = request.POST.get('password')
        p2 = request.POST.get('confirm_password')
        
        if p1 == p2:
            fn = request.session.get('reg_first')
            ln = request.session.get('reg_last')
            age = request.session.get('reg_age')
            nat = request.session.get('reg_nationality')
            email = request.session.get('reg_email')
            phone = request.session.get('reg_phone')

            doc_id = request.session.get('reg_doctor_id')

            generated_username = email.split('@')[0]
            
            if not User.objects.filter(username=generated_username).exists():
                user = User.objects.create_user(username=generated_username, email=email, password=p1)
                user.first_name = fn
                user.last_name = ln
                user.save()

                assigned_doc = User.objects.get(id=doc_id) if doc_id else None
                
                UserProfile.objects.create(user=user, age=age, nationality=nat, phone=phone, assigned_doctor=assigned_doc)
                request.session.flush()
                login(request, user)
                return redirect('dashboard')
    return render(request, 'records/register_step2.html')

# LOGIN LOGIC
# LOGIN LOGIC (Ab Email se chalega)
def login_user(request):
    if request.method == 'POST':
        e = request.POST.get('email')    # Frontend se email uthaya
        p = request.POST.get('password') # Password uthaya
        
        # Smart Logic: Database mein is email wale user ko dhoondho
        user_obj = User.objects.filter(email=e).first()
        
        if user_obj:
            u = user_obj.username # Agar email mil gaya, toh uska chupa hua username nikal lo
        else:
            u = None # Email database mein nahi hai
            
        # Ab Django ko verify karne do
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard') # Doctor ko clinic bhejo
            else:
                return redirect('dashboard')       # Patient ko ghar bhejo
                
        else:
            return render(request, 'records/login.html', {'error': 'Invalid email or password'})
    
    return render(request, 'records/login.html')

# LOGOUT LOGIC
def logout_user(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('home')

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import update_session_auth_hash # password hash karne ki library

@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # 1. Check if Old Password is correct
        if not request.user.check_password(old_password):
            messages.error(request, 'Incorrect old password! ')
            return redirect('dashboard')

        # 2. Check if New and Confirm Passwords match
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match! ')
            return redirect('dashboard')

        # 3. Save the New Password
        request.user.set_password(new_password)
        request.user.save()

        # 4. Keep the user logged in after password change
        update_session_auth_hash(request, request.user)
        
        messages.success(request, 'Password changed successfully! ')
        return redirect('dashboard')
        
    return redirect('dashboard')



def home(request):
    return render(request, 'records/landing.html')


def profile(request):
    return render(request, 'records/profile.html')

@login_required(login_url='login')
def save_habits(request):
    if request.method == 'POST' and request.user.is_authenticated:
        data = json.loads(request.body)
        habit_obj, created = DietHabit.objects.get_or_create(user=request.user)
        habit_obj.habit_json = json.dumps(data)
        habit_obj.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


# 1. Dashboard View ko update karo
@login_required(login_url='login')
def dashboard(request):
    # Dashboard load hote time user ki extra profile details nikal lo
    user_profile = UserProfile.objects.filter(user=request.user).first()
    # 2. Total Reports count karo (Sirf is login user ki)
    total_reports_count = MedicalRecord.objects.filter(patient=request.user).count()

    habit_obj = DietHabit.objects.filter(user=request.user).first()
    all_doctors = User.objects.filter(is_staff=True, is_superuser=False)
    user_habits = habit_obj.habit_json if habit_obj else "[]"
    # Ye profile dashboard.html mein pass kar do
    # 3. Context mein daal kar HTML ko bhej do
    if habit_obj:
        # NAYA LOGIC SHURU: Mahina aur Saal dono check karne ka jadoo 
        current_time = timezone.now()
        current_month = current_time.month
        current_year = current_time.year # NAYI LINE: Current saal nikalo
        
        # NAYI LINE: Agar habit mein date save hai, aur (Mahina alag hai YA Saal alag hai)
        if habit_obj.last_updated and (habit_obj.last_updated.month != current_month or habit_obj.last_updated.year != current_year):
            habit_obj.habit_json = "[]"  # Data saaf karke wapas list bana do
            habit_obj.save()             # Database mein naya empty data save kar do
            
        user_habits = habit_obj.habit_json
    context = {
        'profile': user_profile,
        'total_reports': total_reports_count, # NAYA VARIABLE
        'user_habits': user_habits, # NAYA VARIABLE
        'all_doctors': all_doctors, # NAYA VARIABLE
    }
    return render(request, 'records/dashboard.html', context)

# 2. Edit Profile Save karne ka logic
@login_required(login_url='login')
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        profile = UserProfile.objects.get(user=user)

        # 1. Basic User Info Update
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.save()

        # 2. Custom Profile Info Update
        profile.age = request.POST.get('age')
        profile.phone = request.POST.get('phone')
        profile.nationality = request.POST.get('nationality')
        
        # 3. SMART CLINIC LOGIC (Ye naya part hai)
        new_doctor_id = request.POST.get('assigned_doctor')
        
        if new_doctor_id == "none":
            # Agar user ne 'Individual' select kiya hai, toh assigned doctor hata do
            profile.assigned_doctor = None
            
        elif new_doctor_id:
            # Agar koi valid ID aayi hai, toh usko verify karke assign karo
            valid_doctor = User.objects.filter(id=new_doctor_id, is_staff=True, is_superuser=False).first()
            if valid_doctor:
                profile.assigned_doctor = valid_doctor
            else:
                messages.error(request, "Invalid Clinic/Doctor selected.")
                return redirect('dashboard')

        # 4. Ab saari details (Age, Phone, aur Doctor) ek sath save kar do!
        profile.save()

        messages.success(request, 'Profile updated successfully! ✨')
        
    # Data save hone ke baad wapas dashboard par bhej do
    return redirect('dashboard')


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import json
from .models import MedicalRecord 

@login_required(login_url='login')
def upload_report(request):
    if request.method == 'POST':
        # 1. HTML form se photo nikalna
        image_file = request.FILES.get('report_image')

        if image_file:
            # 2. Database mein naya record banana (Pehle photo save karni zaroori hai)
            record = MedicalRecord.objects.create(
                patient=request.user,       
                report_image=image_file     
            )
            record.save() # Photo tere folder mein chali gayi
            
            
            
                # A. Photo ko folder se open karo
            
           # A. File ka path check karo ki PDF hai ya Image
            file_path = record.report_image.path
            
            if file_path.lower().endswith('.pdf'):
                # Agar PDF hai, toh pehla page Image bana do
                pdf_document = fitz.open(file_path)
                first_page = pdf_document.load_page(0)
                pix = first_page.get_pixmap()
                img = PIL.Image.open(io.BytesIO(pix.tobytes()))
                pdf_document.close() # Memory free karne ke liye
            else:
                # Agar Image hai, toh direct khol lo
                img = PIL.Image.open(file_path)

            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            
            ai_prompt = """
            You are an expert medical data extractor. Read this medical report image.
            1. Identify the type of report (e.g., Blood Test, Lipid Profile, etc.).
            2. Extract all important medical parameters and their values.
            3. Ignore patient name, hospital name, and contact details for privacy.
            4. IMPORTANT: ALWAYS use these exact keys in the 'Data' object if you find the respective values: "age", "blood_pressure", "glucose", "cholesterol". If a value is missing, do not include the key.
            Return ONLY a valid JSON object in this exact format, without any extra text or markdown:
            {"Report_Type": "Name", "Data": {"Hemoglobin": "14", "Sugar": "120"}}
            """

            max_retries = 3  # Hum 3 baar try karenge
            
            for attempt in range(max_retries):
                try:
                    print(f"Attempt {attempt + 1}: AI se data maang rahe hain...")
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[ai_prompt, img]
                    )
                    
                    # Agar yahan tak aa gaya, matlab Data mil gaya.
                    record.extracted_data = response.text
                    record.status = 'success'
                    record.save() 
                    
                    messages.success(request, 'Report uploaded AND analyzed successfully! ')
                    break  # Success milte hi loop se bahar aa jao
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"Error on attempt {attempt + 1}: {error_msg}")
                    
                    # Agar Google busy hai (UNAVAILABLE ya 429 error), toh wait karke dobara try karo
                    if "UNAVAILABLE" in error_msg or "429" in error_msg or "high demand" in error_msg.lower():
                        if attempt < max_retries - 1: # Agar aakhiri try nahi tha
                            print("Google is busy ,waiting for 3 seconds before retrying...")
                            time.sleep(3) # 3 second ruko aur phir try karo
                            continue # Loop ko aage badhao
                    record.status = 'failed' # <-- new LINE
                    record.save() # <-- new LINE yahan bhi save karna zaroori hai taaki status update ho jaye

                    # Agar koi aur hi error hai, ya 3 baar fail ho chuka hai, toh warning de do
                    messages.warning(request, 'Server is experiencing extremely high demand. The report is saved, but AI extraction failed. Please try again later.')
                    break
           
            

            # 3. 'vault' page par bhej dena
            return redirect('vault') 
            
        else:
            messages.error(request, 'Please select an image or PDF file.')

    return render(request, 'records/upload.html')


#Sorter function jo reports ke naam ko clean karega or simmilar reports ko ek category mein daal dega
def get_standard_category(raw_name):
    if not raw_name: return "Other Reports"
    name = raw_name.lower()
    
    if any(word in name for word in ['sugar', 'glucose', 'fasting', 'pp', 'hba1c', 'diabetes']):
        return "Diabetes/Sugar "
    elif any(word in name for word in ['heart', 'ecg', 'lipid', 'cholesterol']):
        return "Heart & Lipid Profile"
    elif any(word in name for word in ['cbc', 'blood']):
        return "Blood Tests (CBC)"
    return raw_name.title()

@login_required(login_url='login')
def my_vault(request):
    user_reports = MedicalRecord.objects.filter(patient=request.user).order_by('-uploaded_at')
    report_categories = set()
    
    for record in user_reports:
        if record.extracted_data:  
            try:
                record.parsed_data = json.loads(record.extracted_data) 
                
                if record.status == 'success' and isinstance(record.parsed_data, dict):
                    # Purana naam liya, usko saaf kiya, aur naya naam HTML ke liye save kar diya
                    raw_type = record.parsed_data.get('Report_Type', 'Other Reports')
                    standard_type = get_standard_category(raw_type)
                    
                    record.parsed_data['Standard_Category'] = standard_type # HTML isko read karega
                    report_categories.add(standard_type) # Sidebar mein clean naam jayega
                        
            except Exception as e:
                print(f"JSON Error: {e}")
                record.parsed_data = None
        else:
            record.parsed_data = None

    context = {
        'reports': user_reports,
        'categories': sorted(list(report_categories)) 
    }
    return render(request, 'records/vault.html', context)




# @login_required(login_url='login')
# def delete_report(request, report_id):
#     # 1. Report dhoondho
#     report = get_object_or_404(MedicalRecord, id=report_id, patient=request.user)
    
#     # 2. Database se udane se pehle, laptop ke folder se photo delete karo
#     if report.report_image:
#         image_path = report.report_image.path
#         if os.path.exists(image_path):
#             os.remove(image_path) # Ye command asli file ko kachre ke dabbe mein daal degi

#     # 3. Ab database wali row delete karo
#     report.delete()
    
#     # 4. Success message aur redirect
#     messages.success(request, 'Report and image permanently deleted!')
#     return redirect('vault')

@login_required(login_url='login')
def delete_report(request, report_id):
    # 1. Report dhoondho
    report = get_object_or_404(MedicalRecord, id=report_id, patient=request.user)
    
    # 2. Database se udane se pehle, photo delete karo (Cloud-safe method)
    if report.report_image:
        report.report_image.delete(save=False) # Ye local aur cloud dono jagah perfectly chalega

    # 3. Ab database wali row delete karo
    report.delete()
    
    # 4. Success message aur redirect
    messages.success(request, 'Report and image permanently deleted!')
    return redirect('vault')


@login_required(login_url='login')
def risk_analysis(request):
    # Default active tab diabetes rahega
    context = {'active_tab': 'diabetes'}
    
    # AUTO-FILL LOGIC
    if request.method == 'GET':
        try:
            latest_report = MedicalRecord.objects.filter(patient=request.user, status='success').order_by('-uploaded_at').first()
            if latest_report and latest_report.extracted_data:
                data = json.loads(latest_report.extracted_data)
                context['prefill_data'] = data.get('Data', {})
                context['auto_filled'] = True
        except Exception as e:
            print(f"Auto-fill error: {e}")

    # PREDICTION LOGIC
    if request.method == 'POST':
        # check karenge ki kis form ka submit button daba
        form_type = request.POST.get('form_type')
        context['active_tab'] = form_type # Jisse page refresh hone par wahi tab khula rahe
        
        try:
            if form_type == 'diabetes':
                pregnancies = float(request.POST.get('pregnancies', 0))
                glucose = float(request.POST.get('glucose', 0))
                bp = float(request.POST.get('bp', 0))
                skin = float(request.POST.get('skin', 0))
                insulin = float(request.POST.get('insulin', 0))
                bmi = float(request.POST.get('bmi', 0))
                dpf = float(request.POST.get('dpf', 0.5))
                age = float(request.POST.get('age', 0))

                diabetes_data = [pregnancies, glucose, bp, skin, insulin, bmi, dpf, age]

                # Yahan prediction aur confidence dono nikal kar context mein daala
                result_dict= get_diabetes_risk(diabetes_data)
                if result_dict:
                       context['diabetes_pred'] = result_dict['risk_status']
                       context['diabetes_confidence'] = result_dict['confidence']
                context['diabetes_submitted'] = True

            elif form_type == 'heart':
                age = float(request.POST.get('age', 0))
                sex = float(request.POST.get('sex', 0))
                cp = float(request.POST.get('cp', 0))
                bp = float(request.POST.get('bp', 0))
                chol = float(request.POST.get('chol', 0))
                glucose = float(request.POST.get('glucose', 100))
                fbs = 1.0 if glucose > 120 else 0.0
                restecg = float(request.POST.get('restecg', 0))
                thalach = float(request.POST.get('thalach', 0))
                exang = float(request.POST.get('exang', 0))
                oldpeak = float(request.POST.get('oldpeak', 0.0))
                slope = float(request.POST.get('slope', 0))
                ca = float(request.POST.get('ca', 0))
                thal = float(request.POST.get('thal', 0))

                # 22-Column Adapter
                heart_data = [0] * 22
                heart_data[1], heart_data[2], heart_data[3], heart_data[4], heart_data[5], heart_data[6] = age, bp, chol, thalach, oldpeak, ca
                heart_data[8] = 1 if sex == 1.0 else 0
                if cp == 1.0: heart_data[12] = 1
                elif cp == 2.0: heart_data[13] = 1
                elif cp == 0.0: heart_data[14] = 1
                heart_data[15] = fbs
                if restecg == 0.0: heart_data[16] = 1
                elif restecg == 1.0: heart_data[17] = 1
                heart_data[18] = exang
                if slope == 1.0: heart_data[19] = 1
                elif slope == 0.0: heart_data[20] = 1
                if thal in [0.0, 1.0]: heart_data[21] = 1

                #Yahan again same logic se prdiction or confidence
                result_dict = get_heart_risk(heart_data)
                if result_dict:
                    context['heart_pred'] = result_dict['risk_status']
                    context['heart_conf'] = result_dict['confidence']
                context['heart_submitted'] = True

        except Exception as e:
            context['error'] = "Data processing error."
            
    return render(request, 'records/risk_analysis.html', context)



from django.http import JsonResponse
@login_required(login_url='login')
def smart_diet(request):
    if request.method == 'GET':
        return render(request, 'records/diet_plan.html')

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            diet_type = data.get('diet_preference', 'veg')
            allergies = data.get('allergies', '')

            # Sabse latest success wali report nikalo
            latest_record = MedicalRecord.objects.filter(
                patient=request.user, 
                status='success'
            ).order_by('-uploaded_at').first()

            if latest_record and latest_record.extracted_data:
                latest_health_profile = latest_record.extracted_data
            else:
                latest_health_profile = "No recent medical reports available. Provide general healthy dietary recommendations for an average adult."

            # Diet aur Allergy rules
            diet_instruction = ""
            if diet_type == 'veg':
                diet_instruction = "Strictly Pure Vegetarian (Plant-based + Dairy). DO NOT suggest meat, fish, or eggs."
            elif diet_type == 'egg':
                diet_instruction = "Eggetarian (Ovo-Vegetarian). Suggest a balanced vegetarian diet and INCLUDE EGGS for protein. DO NOT suggest chicken, meat, or fish."
            elif diet_type == 'nonveg':
                diet_instruction = "Non-Vegetarian. Include a healthy mix of vegetables, lean meats (chicken/fish), and eggs."

            allergy_instruction = f"CRITICAL ALLERGY WARNING: The user is allergic to {allergies}. DO NOT suggest anything containing these." if allergies else "No known allergies."

            # PROMPT UPDATE: Strict "diet plan" ki jagah "recommendations" manga hai
            ai_prompt = f"""
            You are an expert clinical nutritionist. Provide dietary recommendations based on this extracted medical report JSON:
            {latest_health_profile}
            
            Diet Preference: {diet_instruction}
            Allergies: {allergy_instruction}

            Do not provide a strict day-wise meal plan. Just provide general recommendations on what to eat and avoid.
            Return ONLY a valid JSON object. No markdown, no formatting tags, no extra text. Use exactly this format:
            {{
                "analysis": "1-2 lines explaining why these recommendations fit their medical report.",
                "super_foods": ["Food 1 (Reason)", "Food 2 (Reason)", "Food 3 (Reason)"],
                "risk_foods": ["Food 1 (Reason)", "Food 2 (Reason)", "Food 3 (Reason)"]
            }}
            """

            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[ai_prompt]
                    )
                    
                    # Markdown tags hatana
                    clean_text = response.text.replace("```json", "").replace("```", "").strip()
                    ai_result = json.loads(clean_text)
                    
                    return JsonResponse({'status': 'success', 'data': ai_result})
                
                except Exception as e:
                    error_msg = str(e)
                    if "UNAVAILABLE" in error_msg or "429" in error_msg:
                        if attempt < max_retries - 1:
                            time.sleep(2)
                            continue
                    return JsonResponse({'status': 'error', 'message': 'AI Server busy. Please try again.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
       
# Ye function check karega ki user admin hai ya nahi
def is_admin(user):
    return user.is_staff

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='dashboard')
def admin_dashboard(request):
    # 1. TIGHT SECURITY: Sirf is logged-in doctor ke patients uthao!
    my_patients_profiles = UserProfile.objects.filter(assigned_doctor=request.user)

    # 2. SMART SEARCH BAR LOGIC
    search_query = request.GET.get('q', '') # HTML search bar se 'q' uthayega
    if search_query:
        # Agar doctor ne kuch search kiya hai, toh filter karo
        my_patients_profiles = my_patients_profiles.filter(
            Q(patient_id__icontains=search_query) | 
            Q(user__first_name__icontains=search_query) | 
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )

    # 3. VULNERABILITY / RISK ENGINE
    dashboard_data = []
    for profile in my_patients_profiles:
        patient_user = profile.user
        
        # Patient ki total reports count karo
        total_reports = MedicalRecord.objects.filter(patient=patient_user).count()
        
        # Basic Risk Logic: Agar ek bhi report nahi hai, toh Red Zone (Needs Attention)
        # (Baad mein hum yahan DietHabit ka logic bhi daal sakte hain)
        health_status = 'Safe'
        if total_reports == 0:
            health_status = 'No Reports'
        else:
            health_status = "Reports Available"

        dashboard_data.append({
            'profile': profile,
            'total_reports': total_reports,
            'status': health_status,
        })

    context = {
        'dashboard_data': dashboard_data,
        'search_query': search_query,
    }
    
    return render(request, 'records/admin_dashboard.html', context)


@login_required(login_url='login')
def patient_file(request, patient_id):
    # 1. SECURITY CHECK: Sirf doctor is page ko access kar sakta hai
    if not request.user.is_staff:
        messages.error(request, "Access Denied! Only doctors can view patient files.")
        return redirect('vault') # Patient ko uske vault par wapas bhej do
    
    # 2. Patient ko dhoondho
    patient_user = get_object_or_404(User, id=patient_id)
    patient_profile = get_object_or_404(UserProfile, user=patient_user)
    
    # 3. DOCTOR NE DAWAI LIKHI (POST REQUEST)
    if request.method == 'POST':
        symptoms = request.POST.get('symptoms', '').strip()
        diagnosis = request.POST.get('diagnosis', '').strip()
        medicines = request.POST.get('medicines')
        notes = request.POST.get('notes')
        
        # Symptoms aur Diagnosis ko smart tareeqe se combine kardiya
        combined_text = ""
        if symptoms and diagnosis:
            combined_text = f"Symptoms: {symptoms} | Diagnosis: {diagnosis}"
        elif symptoms:
            combined_text = f"Symptoms: {symptoms}"
        elif diagnosis:
            combined_text = f"Diagnosis: {diagnosis}"
        
        # Dawai ka box khali nahi hona chahiye
        if medicines and medicines.strip(): 
            Prescription.objects.create(
                patient=patient_user,
                doctor=request.user,
                diagnosis_or_symptoms=combined_text,
                medicines=medicines,
                notes=notes
            )
            messages.success(request, f"Prescription saved successfully for {patient_user.first_name}!")
            return redirect('patient_file', patient_id=patient_id)
        else:
            messages.error(request, "Medicines field cannot be empty!")

    # 4. PATIENT KI HISTORY NIKALO (Latest sabse upar aayegi)
    past_prescriptions = Prescription.objects.filter(patient=patient_user).order_by('-created_at')
    

    # Paginator ko bolo ki har page pe sirf 5 parchiyan dikhani hain
    paginator = Paginator(past_prescriptions, 5) 
    page_number = request.GET.get('pres_page')
    past_prescriptions = paginator.get_page(page_number)

   # 5. Patient ke saare reports nikal lo (Latest sabse upar)
    patient_reports = MedicalRecord.objects.filter(patient=patient_user).order_by('-uploaded_at')
    
    # --- REPORTS PAGINATION (6 per page) ---
    all_reports = MedicalRecord.objects.filter(patient=patient_user).order_by('-uploaded_at')
    rep_paginator = Paginator(all_reports, 6)
    rep_page = request.GET.get('rep_page')
    patient_reports = rep_paginator.get_page(rep_page)

    sugar_dates = []
    sugar_values = []
    
    # Sirf 'success' wali reports jinka data aa chuka hai (Purani se nayi ki taraf)
    graph_reports = MedicalRecord.objects.filter(patient=patient_user, status='success').order_by('uploaded_at')
    
    for rep in graph_reports:
        if rep.extracted_data:
            try:
                data = json.loads(rep.extracted_data)
                metrics = data.get('Data', {})
                
                # Dictionary mein 'sugar' ya 'glucose' dhoondho
                for key, val in metrics.items():
                    if 'sugar' in key.lower() or 'glucose' in key.lower():
                        nums = re.findall(r'\d+\.?\d*', str(val))
                        if nums:
                            # Date format: e.g., '10 May'
                            sugar_dates.append(rep.uploaded_at.strftime("%d %b, %I:%M %p")) 
                            sugar_values.append(float(nums[0]))
                            break 
            except Exception as e:
                pass

    cbc_dates = []
    hb_values = []
    wbc_values = []
    rbc_values = []
    platelet_values = []

    for rep in graph_reports:
        if rep.extracted_data:
            try:
                data = json.loads(rep.extracted_data)
                metrics = data.get('Data', {})
                
                is_cbc = False
                hb, wbc, rbc, plat = None, None, None, None
                
                for key, val in metrics.items():
                    k = key.lower()
                    nums = re.findall(r'\d+\.?\d*', str(val))
                    if not nums: continue
                    val_float = float(nums[0])
                    
                    if 'hemo' in k or 'hb' in k: 
                        hb = val_float; is_cbc = True
                    elif 'wbc' in k or 'white' in k:
                        wbc = val_float; is_cbc = True
                    elif 'rbc' in k or 'red' in k:
                        rbc = val_float; is_cbc = True
                    elif 'platelet' in k:
                        plat = val_float; is_cbc = True
                
                # Agar in 4 mein se ek bhi value mili, toh isko graph mein dalenge
                if is_cbc:
                    cbc_dates.append(rep.uploaded_at.strftime("%d %b, %I:%M %p"))
                    hb_values.append(hb)
                    wbc_values.append(wbc)
                    rbc_values.append(rbc)
                    platelet_values.append(plat)
            except Exception as e:
                pass

    context = {
        'patient_profile': patient_profile,
        'past_prescriptions': past_prescriptions,
        'patient_reports': patient_reports,
        'active_tab': request.GET.get('tab', 'prescriptions'),

        'sugar_dates': json.dumps(sugar_dates), 
        'sugar_values': json.dumps(sugar_values),

        'cbc_dates': json.dumps(cbc_dates),
        'hb_values': json.dumps(hb_values),
        'wbc_values': json.dumps(wbc_values),
        'rbc_values': json.dumps(rbc_values),
        'platelet_values': json.dumps(platelet_values)


    }
    return render(request, 'records/patient_file.html', context)


@login_required(login_url='login')
def my_prescriptions(request):
    # Sirf us patient ki history nikalo jo login hai
    my_history = Prescription.objects.filter(patient=request.user).order_by('-created_at')
    
    # -- PAGINATION LOGIC SHURU ---
    # Paginator 1 page pe sirf 5 prescriptions dikhani hain
    paginator = Paginator(my_history, 5) 
    page_number = request.GET.get('page') # URL se page number uthao (e.g., ?page=2)
    past_prescriptions = paginator.get_page(page_number)
    # --------------------------------------------

    context = {
        'past_prescriptions': past_prescriptions
    }
    return render(request, 'records/my_prescriptions.html', context)
