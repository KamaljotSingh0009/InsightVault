import os
import json
import time 
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from django.contrib import messages
from .models import MedicalRecord
from google import genai
from dotenv import load_dotenv
import PIL.Image

load_dotenv()


# STEP 1: Basic Info
def register_step1(request):
    if request.method == 'POST':
        request.session['reg_first'] = request.POST.get('first_name')
        request.session['reg_last'] = request.POST.get('last_name')
        request.session['reg_age'] = request.POST.get('age')
        request.session['reg_nationality'] = request.POST.get('nationality')
        request.session['reg_email'] = request.POST.get('email')
        request.session['reg_phone'] = request.POST.get('phone')
        return redirect('register_step2')
    return render(request, 'records/register_step1.html')

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
            
            generated_username = email.split('@')[0]
            
            if not User.objects.filter(username=generated_username).exists():
                user = User.objects.create_user(username=generated_username, email=email, password=p1)
                user.first_name = fn
                user.last_name = ln
                user.save()
                
                UserProfile.objects.create(user=user, age=age, nationality=nat, phone=phone)
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
            return redirect('dashboard')
        else:
            # Agar details galat hain, toh wapas login page pe hi rakho
            return render(request, 'records/login.html', {'error': 'Invalid email or password'})
            
    return render(request, 'records/login.html')

# LOGOUT LOGIC
def logout_user(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('home')

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
            
            img = PIL.Image.open(record.report_image.path)
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            
            ai_prompt = """
            You are an expert medical data extractor. Read this medical report image.
            1. Identify the type of report (e.g., Blood Test, Lipid Profile, etc.).
            2. Extract all important medical parameters and their values.
            3. Ignore patient name, hospital name, and contact details for privacy.
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
                    
                    messages.success(request, 'Report uploaded AND analyzed successfully! 🚀')
                    break  # Success milte hi loop se bahar aa jao
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"Error on attempt {attempt + 1}: {error_msg}")
                    
                    # Agar Google busy hai (UNAVAILABLE ya 429 error), toh wait karke dobara try karo
                    if "UNAVAILABLE" in error_msg or "429" in error_msg or "high demand" in error_msg.lower():
                        if attempt < max_retries - 1: # Agar aakhiri try nahi tha
                            print("Google busy hai. 3 seconds wait karke dobara try kar rahe hain... ⏳")
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
            messages.error(request, 'Please select an image file.')

    return render(request, 'records/upload.html')


def home(request):
    return render(request, 'records/landing.html')


def profile(request):
    return render(request, 'records/profile.html')

@login_required(login_url='login')
def dashboard(request):
    return render(request, 'records/dashboard.html')


@login_required(login_url='login')
def my_vault(request):
    # 1. Login kiye hue user ki saari reports DB se nikalna 
    # (order_by('-uploaded_at') se sabse nayi report sabse upar aayegi)
    user_reports = MedicalRecord.objects.filter(patient=request.user).order_by('-uploaded_at')
    
    for record in user_reports:
        if record.extracted_data:  # Agar AI ne data nikala hai toh
            try:
                # Text ko proper Dictionary mein badal kar ek naye variable mein daal do
                record.parsed_data = json.loads(record.extracted_data) 
            except Exception as e:
                print(f"JSON Error: {e}")
                record.parsed_data = None
        else:
            record.parsed_data = None

    # 2. In reports ko ek dictionary mein pack karke HTML ko bhej dena
    context = {
        'reports': user_reports
    }
    return render(request, 'records/vault.html', context)




@login_required(login_url='login')
def delete_report(request, report_id):
    # 1. Report dhoondho
    report = get_object_or_404(MedicalRecord, id=report_id, patient=request.user)
    
    # --- NAYA LOGIC SHURU ---
    # 2. Database se udane se pehle, laptop ke folder se photo delete karo
    if report.report_image:
        image_path = report.report_image.path
        if os.path.exists(image_path):
            os.remove(image_path) # Ye command asli file ko kachre ke dabbe mein daal degi
    # --- NAYA LOGIC KHATAM ---

    # 3. Ab database wali row delete karo
    report.delete()
    
    # 4. Success message aur redirect
    messages.success(request, 'Report and image permanently deleted!')
    return redirect('vault')


