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
    
# 
# class ForgotPasswordView(APIView):
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
            html_message = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #10b981; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f9f9f9; }}
                    .button {{ display: inline-block; background-color: #10b981; color: white; text-decoration: none; padding: 10px 20px; border-radius: 5px; margin-top: 20px; }}
                    .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #777; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>STINS</h1>
                    </div>
                    <div class="content">
                        <p>Bonjour {user.first_name},</p>
                        <p>Vous avez demandé la réinitialisation de votre mot de passe sur STINS.</p>
                        <p>Veuillez cliquer sur le bouton ci-dessous pour réinitialiser votre mot de passe :</p>
                        <p style="text-align: center;">
                            <a href="{reset_url}" class="button">Réinitialiser mon mot de passe</a>
                        </p>
                        <p>Si le bouton ne fonctionne pas, vous pouvez copier et coller le lien suivant dans votre navigateur :</p>
                        <p>{reset_url}</p>
                        <p>Si vous n'avez pas demandé cette réinitialisation, veuillez ignorer cet email.</p>
                        <p>Cordialement,<br>L'équipe STINS</p>
                    </div>
                    <div class="footer">
                        &copy; 2025 STINS. Tous droits réservés.
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Message texte simple pour les clients qui ne supportent pas HTML
            plain_message = f"""
            Bonjour {user.first_name},
            
            Vous avez demandé la réinitialisation de votre mot de passe sur STINS.
            
            Veuillez cliquer sur le lien suivant pour réinitialiser votre mot de passe :
            {reset_url}
            
            Si vous n'avez pas demandé cette réinitialisation, veuillez ignorer cet email.
            
            Cordialement,
            L'équipe STINS
            """
            
            # Envoyer l'email avec le contenu HTML et texte
            from django.core.mail import EmailMultiAlternatives
            email_message = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email_message.attach_alternative(html_message, "text/html")
            email_message.send(fail_silently=False)
            
            return Response({"message": "Un email de réinitialisation a été envoyé."}, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            # Pour des raisons de sécurité, ne pas indiquer si l'email existe ou non
            return Response({"message": "Un email de réinitialisation a été envoyé si l'adresse existe."}, status=status.HTTP_200_OK)
        except Exception as e:
            # Log l'erreur pour le débogage
            print(f"Erreur d'envoi d'email: {str(e)}")
            return Response({"error": "Une erreur s'est produite lors de l'envoi de l'email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class ResetPasswordView(APIView):
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
class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        # Afficher les données reçues pour le débogage
        print("Données reçues:", request.data)
        
        email = request.data.get('email')
        
        # Vérifier si l'email est présent
        if not email:
            return Response({"error": "L'adresse e-mail est requise."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            
            # Générer un token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Construire l'URL de réinitialisation
            reset_url = f"{settings.SITE_URL}/reset-password/{uid}/{token}/"
            
            # Pour le développement, afficher simplement l'URL dans la console
            print(f"URL de réinitialisation pour {email}: {reset_url}")
            
            # Envoyer l'email (en mode développement, cela sera affiché dans la console)
            subject = 'Réinitialisation de votre mot de passe STINS'
            message = f"""
            Bonjour {user.first_name},
            
            Vous avez demandé la réinitialisation de votre mot de passe sur STINS.
            
            Veuillez cliquer sur le lien suivant pour réinitialiser votre mot de passe :
            {reset_url}
            
            Si vous n'avez pas demandé cette réinitialisation, veuillez ignorer cet email.
            
            L'équipe STINS
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                print(f"Email envoyé avec succès à {email}")
            except Exception as e:
                print(f"Erreur lors de l'envoi de l'email: {str(e)}")
                # En développement, on continue même si l'email n'est pas envoyé
            
            return Response({"message": "Un email de réinitialisation a été envoyé."}, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            # Pour des raisons de sécurité, ne pas indiquer si l'email existe ou non
            print(f"Utilisateur avec l'email {email} n'existe pas")
            return Response({"message": "Un email de réinitialisation a été envoyé si l'adresse existe."}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Erreur inattendue: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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
            # Le token est au format "uid/token"
            parts = token.split('/')
            if len(parts) < 2:
                return Response({"error": "Format de token invalide."}, status=status.HTTP_400_BAD_REQUEST)
                
            uid = parts[0]
            token_value = parts[1]
            
            # Décoder l'UID
            uid = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid)
            
            # Vérifier le token
            if not default_token_generator.check_token(user, token_value):
                return Response({"error": "Le lien de réinitialisation est invalide ou a expiré."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Changer le mot de passe
            user.set_password(password)
            user.save()
            
            return Response({"message": "Votre mot de passe a été réinitialisé avec succès."}, status=status.HTTP_200_OK)
            
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
            print(f"Erreur de réinitialisation: {str(e)}")
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
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import SupportMessage

def support_view(request):
    """Vue ultra-simplifiée pour la page de support"""
    
    if request.method == 'POST':
        # Traiter le formulaire de contact
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        message_text = request.POST.get('message')
        
        # Validation simple
        if not all([name, email, message_text]):
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return render(request, 'support.html')
        
        # Enregistrer le message
        SupportMessage.objects.create(
            name=name,
            email=email,
            phone=phone,
            message=message_text
        )
        
        # Message de succès
        messages.success(request, "Votre message a été envoyé avec succès ! Nous vous répondrons bientôt.")
        return redirect('support')
    
    # Afficher le formulaire (pas besoin de passer les FAQ)
    return render(request, 'support.html')    
# Ajouter ces imports et cette vue à votre fichier views.py existant
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import SupportMessage

def support_view(request):
    """Vue pour afficher et traiter le formulaire de support"""
    if request.method == 'POST':
        # Récupérer les données du formulaire
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message_text = request.POST.get('message')
        
        # Vérifier que les champs requis sont remplis
        if not all([first_name, last_name, email, message_text]):
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return render(request, 'support.html')
        
        # Créer un nouveau message de support
        support_message = SupportMessage(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            message=message_text,
            user=request.user if request.user.is_authenticated else None
        )
        support_message.save()
        
        # Envoyer un email de notification (si configuré)
        try:
            # Email à l'administrateur
            admin_subject = f"Nouveau message de support de {first_name} {last_name}"
            admin_message = f"""
            Un nouveau message de support a été reçu :
            
            De: {first_name} {last_name}
            Email: {email}
            Téléphone: {phone or 'Non fourni'}
            
            Message:
            {message_text}
            
            Vous pouvez gérer ce message dans l'administration du site.
            """
            
            # Email de confirmation à l'utilisateur
            user_subject = "Votre message a bien été reçu - STINS Support"
            user_message = f"""
            Bonjour {first_name},
            
            Nous avons bien reçu votre message et nous vous remercions de nous avoir contactés.
            
            Notre équipe de support va traiter votre demande dans les plus brefs délais.
            
            Voici un récapitulatif de votre message :
            
            {message_text}
            
            Cordialement,
            L'équipe STINS
            """
            
            # Envoyer les emails si SEND_EMAILS est activé dans les paramètres
            if hasattr(settings, 'SEND_EMAILS') and settings.SEND_EMAILS:
                send_mail(
                    admin_subject,
                    admin_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],
                    fail_silently=True,
                )
                
                send_mail(
                    user_subject,
                    user_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=True,
                )
        except Exception as e:
            # Logger l'erreur mais ne pas interrompre le processus
            print(f"Erreur d'envoi d'email: {str(e)}")
        
        # Afficher un message de succès
        messages.success(request, "Votre message a été envoyé avec succès. Nous vous répondrons dans les plus brefs délais.")
        return redirect('support_success')
    
    # Si c'est une requête GET, afficher simplement le formulaire
    return render(request, 'support.html')

def support_success_view(request):
    """Vue pour la page de confirmation après envoi du formulaire"""
    return render(request, 'support_success.html')