from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import UserProfile

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
    return redirect('login')

# UPLOAD PAGE LOGIC (Secured)
@login_required(login_url='login')
def upload_report(request):
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
    # Aage chalke hum yahan database se user ki real reports bhejenge
    return render(request, 'records/vault.html')