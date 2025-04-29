from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Watchlist, WatchHistory
from .serializers import (
    UserSerializer, RegisterSerializer, WatchlistSerializer, 
    WatchHistorySerializer
)
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Mettre à jour le type d'abonnement si fourni
        subscription_type = request.data.get('subscription_type')
        if subscription_type in ['basic', 'standard', 'premium']:
            profile = user.profile
            profile.subscription_type = subscription_type
            
            # Définir la date d'expiration à 30 jours à partir d'aujourd'hui
            from datetime import date, timedelta
            profile.subscription_expiry = date.today() + timedelta(days=30)
            profile.save()
        
        token, created = Token.objects.get_or_create(user=user)
        
        # Connecter l'utilisateur
        login(request, user)
        
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": token.key
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user:
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "user": UserSerializer(user).data,
                "token": token.key
            })
        
        return Response({"error": "Identifiants invalides"}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Supprimer le token pour déconnecter l'utilisateur
            request.user.auth_token.delete()
            logout(request)
            return Response({"message": "Déconnexion réussie"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class WatchlistViewSet(viewsets.ModelViewSet):
    serializer_class = WatchlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

class WatchHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = WatchHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return WatchHistory.objects.filter(user=self.request.user)
    
class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            # Générer un token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Construire l'URL de réinitialisation
            reset_url = f"{settings.SITE_URL}/reset-password/{uid}/{token}/"
            
            # Envoyer l'email
            subject = 'Réinitialisation de votre mot de passe STINS'
            message = f"""
            Bonjour {user.first_name},
            
            Vous avez demandé la réinitialisation de votre mot de passe sur STINS.
            
            Veuillez cliquer sur le lien suivant pour réinitialiser votre mot de passe :
            {reset_url}
            
            Si vous n'avez pas demandé cette réinitialisation, veuillez ignorer cet email.
            
            L'équipe STINS
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            return Response({"message": "Un email de réinitialisation a été envoyé."}, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            # Pour des raisons de sécurité, ne pas indiquer si l'email existe ou non
            return Response({"message": "Un email de réinitialisation a été envoyé si l'adresse existe."}, status=status.HTTP_200_OK)

class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        password = request.data.get('password')
        password2 = request.data.get('password2')
        
        if not token or not password or not password2:
            return Response({"error": "Tous les champs sont requis."}, status=status.HTTP_400_BAD_REQUEST)
        
        if password != password2:
            return Response({"error": "Les mots de passe ne correspondent pas."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Extraire l'UID et le token
            uid, token = token.split('/')
            
            # Décoder l'UID
            uid = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid)
            
            # Vérifier le token
            if not default_token_generator.check_token(user, token):
                return Response({"error": "Le lien de réinitialisation est invalide ou a expiré."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Changer le mot de passe
            user.set_password(password)
            user.save()
            
            return Response({"message": "Votre mot de passe a été réinitialisé avec succès."}, status=status.HTTP_200_OK)
            
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Le lien de réinitialisation est invalide."}, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        if not current_password or not new_password or not confirm_password:
            return Response({"error": "Tous les champs sont requis."}, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != confirm_password:
            return Response({"error": "Les nouveaux mots de passe ne correspondent pas."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.check_password(current_password):
            return Response({"error": "Le mot de passe actuel est incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        
        # Mettre à jour la session pour éviter la déconnexion
        update_session_auth_hash(request, user)
        
        return Response({"message": "Votre mot de passe a été changé avec succès."}, status=status.HTTP_200_OK)

class UpdateSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def put(self, request):
        user = request.user
        subscription_type = request.data.get('subscription_type')
        
        if not subscription_type or subscription_type not in ['basic', 'standard', 'premium']:
            return Response({"error": "Type d'abonnement invalide."}, status=status.HTTP_400_BAD_REQUEST)
        
        profile = user.profile
        profile.subscription_type = subscription_type
        
        # Mettre à jour la date d'expiration (30 jours à partir d'aujourd'hui)
        from datetime import date, timedelta
        profile.subscription_expiry = date.today() + timedelta(days=30)
        profile.save()
        
        return Response({
            "message": "Abonnement mis à jour avec succès.",
            "subscription_type": subscription_type,
            "subscription_expiry": profile.subscription_expiry
        }, status=status.HTTP_200_OK)    