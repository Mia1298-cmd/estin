from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

def index(request):
    """Vue pour la page d'accueil"""
    return render(request, 'index.html')

def login_view(request):
    """Vue pour la page de connexion"""
    if request.user.is_authenticated:
        return redirect('index')
    return render(request, 'login.html')

def signup_view(request):
    """Vue pour la page d'inscription"""
    if request.user.is_authenticated:
        return redirect('index')
    return render(request, 'signup.html')

@login_required
def profile_view(request):
    """Vue pour la page de profil utilisateur"""
    return render(request, 'profile.html')

def logout_view(request):
    """Vue pour la déconnexion"""
    logout(request)
    return redirect('index')