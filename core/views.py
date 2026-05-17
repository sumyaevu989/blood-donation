from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Donor, ContactMessage, BloodRequest, BloodBankInventory, BloodCamp
from .forms import DonorRegistrationForm
import random

def leaderboard(request):
    top_donors = Donor.objects.order_by('-total_donations')[:10]
    return render(request, 'core/leaderboard.html', {'top_donors': top_donors})

def camps(request):
    upcoming_camps = BloodCamp.objects.order_by('date')
    return render(request, 'core/camps.html', {'camps': upcoming_camps})

@login_required
def join_camp(request, camp_id):
    camp = get_object_or_404(BloodCamp, id=camp_id)
    if hasattr(request.user, 'donor'):
        camp.participants.add(request.user.donor)
        messages.success(request, f"You successfully joined {camp.name}!")
    else:
        messages.error(request, "Only registered donors can join camps.")
    return redirect('camps')

def verify_otp(request, req_id):
    req = get_object_or_404(BloodRequest, id=req_id)
    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        expected_otp = request.session.get(f'otp_{req_id}')
        if otp_entered and str(otp_entered) == str(expected_otp):
            req.is_verified = True
            req.save()
            messages.success(request, 'Request verified successfully via OTP. It is now published!')
            return redirect('index')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
    return render(request, 'core/otp_verify.html', {'req': req})

def about_view(request):
    return render(request, 'core/about.html')

def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = request.POST.get('subject')
        blood_group = request.POST.get('blood_group')
        message_body = request.POST.get('message')
        
        # Combine everything into the message field for our database model
        full_message = f"Phone: {phone}\nSubject: {subject}\nBlood Group: {blood_group}\n\nMessage:\n{message_body}"
        
        ContactMessage.objects.create(name=name, email=email, message=full_message)
        
        messages.success(request, 'Your message has been sent successfully. We will get back to you soon!')
        return redirect('contact')
        
    return render(request, 'core/contact.html')

def request_blood_view(request):
    if request.method == 'POST':
        patient_name = request.POST.get('patient_name')
        blood_group = request.POST.get('blood_group')
        hospital = request.POST.get('hospital')
        urgency = request.POST.get('urgency')
        contact_number = request.POST.get('contact_number') or 'Not Provided'
        
        req = BloodRequest.objects.create(
            patient_name=patient_name,
            blood_group=blood_group,
            hospital=hospital,
            contact_number=contact_number,
            urgency=urgency,
            is_verified=False
        )
        
        # OTP verification (mock via session)
        otp = random.randint(100000, 999999)
        request.session[f'otp_{req.id}'] = otp
        messages.info(request, f'Mock SMS Sent: Your OTP is {otp}. Please verify your request to publish it.')
        return redirect('verify_otp', req_id=req.id)
        
    # Get all active requests to display them
    requests = BloodRequest.objects.filter(is_verified=True).order_by('-created_at')
    return render(request, 'core/request_blood.html', {'requests': requests})

def index(request):
    donors = Donor.objects.all()
    inventory = BloodBankInventory.objects.all()
    
    blood_group = request.GET.get('bg')
    location = request.GET.get('loc')
    area = request.GET.get('area')
    
    if blood_group:
        donors = donors.filter(blood_group=blood_group)
    if location:
        donors = donors.filter(location__icontains=location)
    if area:
        donors = donors.filter(area__icontains=area)
        
    return render(request, 'core/index.html', {'donors': donors, 'inventory': inventory})

def register_view(request):
    if request.method == 'POST':
        form = DonorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Save the extended Donor profile data
            Donor.objects.create(
                user=user,
                phone=form.cleaned_data['phone'],
                blood_group=form.cleaned_data['blood_group'],
                location=form.cleaned_data['location'],
                area=form.cleaned_data['area']
            )
            login(request, user)
            return redirect('dashboard')
    else:
        form = DonorRegistrationForm()
        
    return render(request, 'core/register.html', {'form': form})

@login_required
def dashboard(request):
    donor_profile = getattr(request.user, 'donor', None)
    # Admin / dashboard statistics
    donors_count = Donor.objects.count()
    requests_count = BloodRequest.objects.count()
    messages_count = ContactMessage.objects.count()
    users_count = User.objects.count()

    context = {
        'donor': donor_profile,
        'donors_count': donors_count,
        'requests_count': requests_count,
        'messages_count': messages_count,
        'users_count': users_count,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.email = request.POST.get('email')
        user.save()
        
        donor_profile = getattr(user, 'donor', None)
        if donor_profile:
            donor_profile.blood_group = request.POST.get('blood_group')
            donor_profile.phone = request.POST.get('phone')
            donor_profile.location = request.POST.get('location')
            donor_profile.area = request.POST.get('area')
            donor_profile.save()
            
        messages.success(request, 'Profile updated successfully!')
    return redirect('dashboard')
