# users/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import Profile
from movies.models import Category

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        required=False
    )
    preferred_genres = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'genre-checkbox'}),
        required=False
    )
    
    class Meta:
        model = Profile
        fields = ['profile_picture', 'cover_photo', 'bio', 'location', 
                  'birth_date', 'phone_number', 'preferred_genres', 'language_preference']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4}),
            'location': forms.TextInput(attrs={'class': 'form-input'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input'}),
            'language_preference': forms.Select(attrs={'class': 'form-select'}),
        }