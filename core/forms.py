from django import forms
from django.contrib.auth.models import User
from .models import Donor

class DonorRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    phone = forms.CharField(max_length=20)
    blood_group = forms.CharField(max_length=5)
    location = forms.CharField(max_length=100)
    area = forms.CharField(max_length=100, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email', 'password']