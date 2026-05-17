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
    last_donation_date = models.DateField(blank=True, null=True)
    total_donations = models.IntegerField(default=0)

    @property
    def is_eligible(self):
        if not self.last_donation_date:
            return True
        return (timezone.now().date() - self.last_donation_date).days >= 90

    @property
    def next_eligible_date(self):
        if not self.last_donation_date:
            return timezone.now().date()
        return self.last_donation_date + timedelta(days=90)

    @property
    def badge(self):
        if self.total_donations >= 10:
            return "Hero 🦸‍♂️"
        elif self.total_donations >= 5:
            return "Gold 🥇"
        elif self.total_donations >= 3:
            return "Silver 🥈"
        elif self.total_donations >= 1:
            return "Bronze 🥉"
        return "Beginner 🌱"

    @property
    def reward_points(self):
        return self.total_donations * 50

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

    def __str__(self):
        return f"{self.blood_group} - {self.bags_available} Bags"

class BloodCamp(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField()
    location = models.CharField(max_length=200)
    description = models.TextField()
    participants = models.ManyToManyField(Donor, blank=True, related_name='camps_joined')

    def __str__(self):
        return self.name
