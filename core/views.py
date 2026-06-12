from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse
from .models import Donor, ContactMessage, BloodRequest, BloodBankInventory, BloodCamp, DonationHistory
from .forms import DonorRegistrationForm
import random
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

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

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils.dateparse import parse_datetime
from django.utils import timezone
import math

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

    # Cool-down filtering (only send eligible donors to context/ajax)
    donors = [d for d in donors if d.is_eligible]
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        donors_data = []
        for d in donors:
            donors_data.append({
                'name': d.user.username,
                'blood_group': d.blood_group,
                'phone': d.phone,
                'location': d.location,
                'area': d.area if d.area else '-',
                'email': d.user.email,
                'last_donation_date': d.last_donation_date.isoformat() if d.last_donation_date else None,
                'days_since_last_donation': d.days_since_last_donation,
                'is_eligible': d.is_eligible,
                'next_eligible_date': d.next_eligible_date.isoformat() if d.next_eligible_date else None,
                'recency': d.donation_recency,
            })
        return JsonResponse({'donors': donors_data})
        
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
        phone = request.POST.get('phone')
        
        # Backend validation for phone number length
        if not phone.isdigit() or len(phone) != 11:
            messages.error(request, 'Phone number must be exactly 11 digits.')
            return redirect('dashboard')
            
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

@login_required
def generate_certificate(request):
    donor = getattr(request.user, 'donor', None)
    if not donor or donor.total_donations < 1:
        messages.error(request, 'You need to donate at least once to get a certificate.')
        return redirect('dashboard')

    buffer = io.BytesBytesIO() if hasattr(io, 'BytesBytesIO') else io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Draw border
    p.setStrokeColor(colors.darkred)
    p.setLineWidth(4)
    p.rect(30, 30, width - 60, height - 60)
    p.setStrokeColor(colors.gold)
    p.setLineWidth(2)
    p.rect(34, 34, width - 68, height - 68)

    # Title
    p.setFont("Helvetica-Bold", 32)
    p.setFillColor(colors.darkred)
    p.drawCentredString(width / 2.0, height - 150, "Certificate of Appreciation")

    # Subtitle
    p.setFont("Helvetica", 18)
    p.setFillColor(colors.black)
    p.drawCentredString(width / 2.0, height - 200, "This certificate is proudly presented to")

    # Name
    p.setFont("Helvetica-Bold", 28)
    p.setFillColor(colors.blue)
    p.drawCentredString(width / 2.0, height - 260, request.user.get_full_name() or request.user.username)

    # Details
    p.setFont("Helvetica", 16)
    p.setFillColor(colors.black)
    p.drawCentredString(width / 2.0, height - 320, f"For proudly donating blood {donor.total_donations} times.")
    p.drawCentredString(width / 2.0, height - 350, f"Current Badge: {donor.badge}")
    p.drawCentredString(width / 2.0, height - 380, "Your contribution has helped save precious lives.")

    # Footer
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width / 2.0, height - 500, "Blood Donation System")
    p.setFont("Helvetica", 12)
    p.drawCentredString(width / 2.0, height - 520, "Official Digital Certificate")

    p.showPage()
    p.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Blood_Donation_Certificate_{request.user.username}.pdf"'
    return response


# --- Donation history JSON API ---
@require_http_methods(['GET', 'POST'])
def donor_donations_api(request, donor_id):
    donor = get_object_or_404(Donor, id=donor_id)

    if request.method == 'GET':
        history = donor.donation_history.all().values('id', 'donation_date', 'location', 'notes', 'created_at')
        data = []
        for h in history:
            data.append({
                'id': h['id'],
                'donation_date': h['donation_date'].isoformat() if h['donation_date'] else None,
                'location': h['location'],
                'notes': h['notes'],
                'created_at': h['created_at'].isoformat() if h['created_at'] else None,
            })
        return JsonResponse({'donations': data})

    # POST -> create new donation (only donor owner or staff)
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        if not (request.user.is_staff or getattr(request.user, 'donor', None) and request.user.donor.id == donor.id):
            return JsonResponse({'error': 'Permission denied'}, status=403)

        try:
            payload = json.loads(request.body.decode('utf-8'))
            donation_date = payload.get('donation_date')
            location = payload.get('location')
            notes = payload.get('notes')
            if not donation_date:
                return JsonResponse({'error': 'donation_date is required'}, status=400)
            dh = DonationHistory.objects.create(
                donor=donor,
                donation_date=donation_date,
                location=location,
                notes=notes
            )
            # Recalculate donor aggregates
            donor.total_donations = donor.donation_history.count()
            latest = donor.donation_history.order_by('-donation_date').first()
            donor.last_donation_date = latest.donation_date if latest else None
            donor.save()

            return JsonResponse({'id': dh.id, 'donation_date': dh.donation_date.isoformat(), 'location': dh.location, 'notes': dh.notes}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(['PUT', 'DELETE'])
def donation_detail_api(request, donation_id):
    dh = get_object_or_404(DonationHistory, id=donation_id)
    donor = dh.donor

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    if not (request.user.is_staff or getattr(request.user, 'donor', None) and request.user.donor.id == donor.id):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if request.method == 'PUT':
        try:
            payload = json.loads(request.body.decode('utf-8'))
            donation_date = payload.get('donation_date')
            location = payload.get('location')
            notes = payload.get('notes')
            if donation_date:
                dh.donation_date = donation_date
            dh.location = location if location is not None else dh.location
            dh.notes = notes if notes is not None else dh.notes
            dh.save()
            # Recalculate donor aggregates
            donor.total_donations = donor.donation_history.count()
            latest = donor.donation_history.order_by('-donation_date').first()
            donor.last_donation_date = latest.donation_date if latest else None
            donor.save()
            return JsonResponse({'id': dh.id, 'donation_date': dh.donation_date.isoformat(), 'location': dh.location, 'notes': dh.notes})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    if request.method == 'DELETE':
        try:
            dh.delete()
            # Recalculate donor aggregates
            donor.total_donations = donor.donation_history.count()
            latest = donor.donation_history.order_by('-donation_date').first()
            donor.last_donation_date = latest.donation_date if latest else None
            donor.save()
            return JsonResponse({'deleted': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


# --- New APIs ---
def camps_api(request):
    camps = BloodCamp.objects.filter(is_active=True).order_by('date')
    data = []
    for c in camps:
        data.append({
            'id': c.id,
            'name': c.name,
            'date': c.date.isoformat(),
            'location': c.location,
            'latitude': c.latitude,
            'longitude': c.longitude,
            'description': c.description,
            'participants': c.participants.count(),
            'capacity': c.capacity,
        })
    return JsonResponse({'camps': data})


def _haversine_distance(lat1, lon1, lat2, lon2):
    # returns distance in kilometers between two lat/lon points
    if None in (lat1, lon1, lat2, lon2):
        return None
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def nearby_donors_api(request):
    try:
        lat = float(request.GET.get('lat'))
        lng = float(request.GET.get('lng'))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'lat and lng query parameters required'}, status=400)

    radius_km = float(request.GET.get('radius_km', 10))
    blood_group = request.GET.get('blood_group')

    donors = Donor.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    if blood_group:
        donors = donors.filter(blood_group=blood_group)

    results = []
    for d in donors:
        if not d.is_eligible:
            continue
        dist = _haversine_distance(lat, lng, d.latitude, d.longitude)
        if dist is None:
            continue
        if dist <= radius_km:
            results.append({
                'id': d.id,
                'name': d.user.username,
                'blood_group': d.blood_group,
                'phone': d.phone,
                'latitude': d.latitude,
                'longitude': d.longitude,
                'distance_km': round(dist, 2),
                'last_donation_date': d.last_donation_date.isoformat() if d.last_donation_date else None,
                'is_eligible': d.is_eligible,
            })

    results.sort(key=lambda x: x['distance_km'])
    return JsonResponse({'donors': results})


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def appointments_api(request):
    # GET -> list appointments for current user (or all for staff)
    if request.method == 'GET':
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        if request.user.is_staff:
            appts = DonationAppointment.objects.all()
        else:
            donor = getattr(request.user, 'donor', None)
            if not donor:
                return JsonResponse({'error': 'Only donors can view appointments'}, status=403)
            appts = donor.appointments.all()

        data = []
        for a in appts:
            data.append({
                'id': a.id,
                'donor': a.donor.user.username,
                'center': a.center.id if a.center else None,
                'camp': a.camp.id if a.camp else None,
                'scheduled_at': a.scheduled_at.isoformat(),
                'status': a.status,
                'reminder_sent': a.reminder_sent,
            })
        return JsonResponse({'appointments': data})

    # POST -> create appointment
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        donor = getattr(request.user, 'donor', None)
        if not donor:
            return JsonResponse({'error': 'Only donors can create appointments'}, status=403)

        payload = json.loads(request.body.decode('utf-8'))
        scheduled_at = payload.get('scheduled_at')
        center_id = payload.get('center_id')
        camp_id = payload.get('camp_id')
        if not scheduled_at:
            return JsonResponse({'error': 'scheduled_at is required (ISO datetime)'}, status=400)
        dt = parse_datetime(scheduled_at)
        if dt is None:
            return JsonResponse({'error': 'Invalid datetime format'}, status=400)
        # ensure timezone-aware
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt)

        center = None
        camp = None
        if center_id:
            from .models import BloodCenter
            center = BloodCenter.objects.filter(id=center_id).first()
        if camp_id:
            from .models import BloodCamp
            camp = BloodCamp.objects.filter(id=camp_id).first()

        appt = DonationAppointment.objects.create(donor=donor, center=center, camp=camp, scheduled_at=dt)
        return JsonResponse({'id': appt.id, 'scheduled_at': appt.scheduled_at.isoformat(), 'status': appt.status}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
