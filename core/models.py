from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# Create your models here.

class Donor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    blood_group = models.CharField(max_length=5)
    location = models.CharField(max_length=100)
    area = models.CharField(max_length=100, blank=True, null=True)
    # optional geolocation for improved matching
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    last_donation_date = models.DateField(blank=True, null=True)
    total_donations = models.IntegerField(default=0)

    @property
    def is_eligible(self):
        if not self.last_donation_date:
            return True
        return (timezone.now().date() - self.last_donation_date).days >= 120

    @property
    def next_eligible_date(self):
        if not self.last_donation_date:
            return timezone.now().date()
        return self.last_donation_date + timedelta(days=120)

    @property
    def days_since_last_donation(self):
        """Return number of days since the last donation or None if unknown."""
        if not self.last_donation_date:
            return None
        return (timezone.now().date() - self.last_donation_date).days

    @property
    def donation_recency(self):
        """Return a recency category: 'recent', 'cooldown', 'eligible', or 'unknown'.

        - 'recent' : donated within last 30 days
        - 'cooldown': donated between 31 and 119 days ago
        - 'eligible': donated 120+ days ago
        - 'unknown': no recorded donation
        """
        if not self.last_donation_date:
            return 'unknown'
        days = self.days_since_last_donation
        if days is None:
            return 'unknown'
        if days <= 30:
            return 'recent'
        if days < 120:
            return 'cooldown'
        return 'eligible'

    @property
    def badge(self):
        if self.total_donations >= 10:
            return "Life Saver 👑"
        elif self.total_donations >= 5:
            return "Silver Donor 🥈"
        elif self.total_donations >= 1:
            return "Bronze Donor 🩸"
        return "Beginner 🌱"

    @property
    def reward_points(self):
        return self.total_donations * 100

    def __str__(self):
        return f"{self.user.username} - {self.blood_group}"

class BloodRequest(models.Model):
    patient_name = models.CharField(max_length=100)
    blood_group = models.CharField(max_length=5)
    hospital = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=20, default='Not Provided')
    urgency = models.CharField(max_length=50)
    ambulance_needed = models.BooleanField(default=False)
    ambulance_contact = models.CharField(max_length=50, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request: {self.patient_name} ({self.blood_group})"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    date_sent = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class BloodBankInventory(models.Model):
    blood_group = models.CharField(max_length=5, unique=True)
    bags_available = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    # optional link to a physical blood center for real-time stock
    center = models.ForeignKey('BloodCenter', on_delete=models.SET_NULL, blank=True, null=True, related_name='inventories')

    def __str__(self):
        return f"{self.blood_group} - {self.bags_available} Bags"

class BloodCamp(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField()
    location = models.CharField(max_length=200)
    # optional geolocation for map display
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    description = models.TextField()
    participants = models.ManyToManyField(Donor, blank=True, related_name='camps_joined')
    capacity = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class DonationHistory(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='donation_history')
    donation_date = models.DateField()
    location = models.CharField(max_length=200, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-donation_date']

    def __str__(self):
        return f"{self.donor.user.username} - {self.donation_date}"


class BloodCenter(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return self.name


class DonationAppointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='appointments')
    center = models.ForeignKey(BloodCenter, on_delete=models.SET_NULL, blank=True, null=True, related_name='appointments')
    camp = models.ForeignKey(BloodCamp, on_delete=models.SET_NULL, blank=True, null=True, related_name='appointments')
    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    reminder_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scheduled_at']

    def __str__(self):
        return f"Appointment for {self.donor.user.username} at {self.scheduled_at}"
