from django.contrib import admin
from django.contrib.auth.models import User
from django.http import HttpResponse
import csv
from django.urls import path
from django.shortcuts import redirect
from .models import Donor, BloodRequest, ContactMessage, BloodBankInventory
from django.db.models import Count, Q
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
from .models import Donor, BloodRequest, ContactMessage, BloodBankInventory, BloodCamp

class CustomAdminSite(admin.AdminSite):
	site_header = 'Blood Donation Admin'
	site_title = 'Blood Donation Admin'
	index_title = 'Welcome to Blood Donation Admin'

	def index(self, request, extra_context=None):
		donors_count = Donor.objects.count()
		requests_count = BloodRequest.objects.count()
		messages_count = ContactMessage.objects.count()
		users_count = User.objects.count()

		recent_requests = BloodRequest.objects.all().order_by('-created_at')[:6]

		# donors per blood group for chart
		donors_by_group_qs = Donor.objects.values('blood_group').annotate(count=Count('id'))
		donors_by_group = {d['blood_group']: d['count'] for d in donors_by_group_qs}

		# urgent requests (ambulance requested or urgency mention)
		urgent_count = BloodRequest.objects.filter(Q(ambulance_needed=True) | Q(urgency__icontains='urgent') | Q(urgency__icontains='emergency')).count()

		stats = {
			'donors_count': donors_count,
			'requests_count': requests_count,
			'messages_count': messages_count,
			'users_count': users_count,
			'recent_requests': recent_requests,
			'donors_by_group': donors_by_group,
			'urgent_count': urgent_count,
		}

		if extra_context:
			extra_context.update(stats)
		else:
			extra_context = stats

		return super().index(request, extra_context=extra_context)

	def get_urls(self):
		urls = super().get_urls()
		custom_urls = [
			path('send-donors-mailto/', self.admin_view(self.send_donors_mailto), name='send-donors-mailto'),
			path('email-donors/', self.admin_view(self.email_donors_view), name='email-donors'),
			path('request-ambulance/', self.admin_view(self.request_ambulance_view), name='request-ambulance'),
		]
		return custom_urls + urls

	def send_donors_mailto(self, request):
		emails = list(Donor.objects.values_list('user__email', flat=True))
		emails = [e for e in emails if e]
		if not emails:
			return redirect('/admin/')
		to = ','.join(emails)
		return redirect(f'mailto:{to}')

	def email_donors_view(self, request):
		# server-side bulk email to all donors (admin form POST)
		if request.method == 'POST':
			subject = request.POST.get('subject', '').strip()
			body = request.POST.get('body', '').strip()
			if not subject or not body:
				messages.error(request, 'Subject and body are required to send email.')
				return redirect('admin:index')

			recipient_list = list(Donor.objects.values_list('user__email', flat=True))
			recipient_list = [e for e in recipient_list if e]
			if not recipient_list:
				messages.error(request, 'No donor email addresses found.')
				return redirect('admin:index')

			try:
				# Use settings.DEFAULT_FROM_EMAIL if set, else SERVER_EMAIL
				from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', getattr(settings, 'SERVER_EMAIL', None))
				if not from_email:
					from_email = None
				send_mail(subject, body, from_email, recipient_list, fail_silently=False)
				messages.success(request, f'Email sent to {len(recipient_list)} donors.')
			except Exception as e:
				messages.error(request, f'Failed to send email: {e}')
			return redirect('admin:index')
		# GET -> show a simple form (should be modal on index)
		return render(request, 'admin/email_donors_form.html', {})

	def request_ambulance_view(self, request):
		# POST: expects 'request_id' and 'ambulance_contact'
		if request.method == 'POST':
			rid = request.POST.get('request_id')
			contact = request.POST.get('ambulance_contact', '').strip()
			if not rid:
				messages.error(request, 'Missing request id')
				return redirect('admin:index')
			try:
				br = BloodRequest.objects.get(pk=int(rid))
				br.ambulance_needed = True
				br.ambulance_contact = contact or br.ambulance_contact
				br.save()
				messages.success(request, f'Ambulance requested for {br.patient_name}.')
			except BloodRequest.DoesNotExist:
				messages.error(request, 'Blood request not found')
			except Exception as e:
				messages.error(request, f'Error: {e}')
		return redirect('admin:index')


# instantiate custom admin site and register models on it
admin_site = CustomAdminSite(name='admin')


class BloodRequestAdmin(admin.ModelAdmin):
	list_display = ('patient_name', 'blood_group', 'hospital', 'urgency', 'ambulance_needed', 'is_verified', 'created_at')
	list_filter = ('blood_group', 'urgency', 'ambulance_needed', 'is_verified')
	list_editable = ('is_verified',)
	actions = ['export_as_csv', 'mark_ambulance_needed', 'match_and_notify_donors']

	def export_as_csv(self, request, queryset):
		meta = self.model._meta
		field_names = [f.name for f in meta.fields]

		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename=bloodrequests.csv'
		writer = csv.writer(response)

		writer.writerow(field_names)
		for obj in queryset:
			writer.writerow([getattr(obj, f) for f in field_names])
		return response
	export_as_csv.short_description = "Export selected requests as CSV"

	def mark_ambulance_needed(self, request, queryset):
		updated = queryset.update(ambulance_needed=True)
		self.message_user(request, f"Marked {updated} request(s) as requiring ambulance")
	mark_ambulance_needed.short_description = "Mark selected requests as ambulance needed"

	def match_and_notify_donors(self, request, queryset):
		for req in queryset:
			# Find eligible donors with same blood group
			# O- can give to anyone, O+ to any positive, but keeping it simple for now: exact match or O-
			compatible_groups = [req.blood_group]
			if req.blood_group != 'O-':
				compatible_groups.append('O-')

			eligible_donors = [d for d in Donor.objects.filter(blood_group__in=compatible_groups) if d.is_eligible]
			emails = [d.user.email for d in eligible_donors if d.user.email]
			
			if emails:
				subject = f"Urgent: {req.blood_group} Blood Required at {req.hospital}"
				body = f"Hello,\n\nAn urgent request for {req.blood_group} blood has been made for {req.patient_name} at {req.hospital}.\nSince your blood group is a match and you are eligible to donate, please log in to your dashboard to help.\n\nThank you,\nBlood Donation System"
				
				from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', getattr(settings, 'SERVER_EMAIL', None))
				try:
					send_mail(subject, body, from_email, emails, fail_silently=True)
					self.message_user(request, f"Matched and notified {len(emails)} donor(s) via Email. [Mock SMS sent to {len(emails)} numbers!]")
				except Exception as e:
					self.message_user(request, f"Failed to send email to matched donors for {req.patient_name}: {e}", level=messages.ERROR)
			else:
				self.message_user(request, f"No eligible donors found for {req.patient_name}'s request.", level=messages.WARNING)
	match_and_notify_donors.short_description = "Match and notify eligible donors via email"


class DonorAdmin(admin.ModelAdmin):
	list_display = ('user', 'blood_group', 'location', 'phone', 'last_donation_date', 'total_donations', 'is_eligible')
	search_fields = ('user__username', 'blood_group', 'location')
	list_filter = ('blood_group', 'location')

	def is_eligible(self, obj):
		return obj.is_eligible
	is_eligible.boolean = True
	is_eligible.short_description = "Eligible?"

class BloodBankInventoryAdmin(admin.ModelAdmin):
	list_display = ('blood_group', 'bags_available', 'last_updated')
	list_editable = ('bags_available',)
	search_fields = ('blood_group',)

class BloodCampAdmin(admin.ModelAdmin):
	list_display = ('name', 'date', 'location')
	filter_horizontal = ('participants',)

class ContactMessageAdmin(admin.ModelAdmin):
	list_display = ('name', 'email', 'date_sent')


class UserAdminWrapper(admin.ModelAdmin):
	pass


admin_site.register(Donor, DonorAdmin)
admin_site.register(BloodRequest, BloodRequestAdmin)
admin_site.register(BloodBankInventory, BloodBankInventoryAdmin)
admin_site.register(BloodCamp, BloodCampAdmin)
admin_site.register(ContactMessage, ContactMessageAdmin)
admin_site.register(User, UserAdminWrapper)

def _send_donors_mailto(request):
	# quick endpoint: redirect to mailto with donor emails
	emails = list(Donor.objects.values_list('user__email', flat=True))
	emails = [e for e in emails if e]
	if not emails:
		return redirect('/admin/')
	to = ','.join(emails)
	return redirect(f'mailto:{to}')

