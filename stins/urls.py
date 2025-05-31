from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import TemplateView
from users.views import ForgotPasswordView, ResetPasswordView

urlpatterns = [
    # URLs pour les pages web (templates HTML)
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('accounts/', include('allauth.urls')),
    path('pricing/', views.pricing, name='pricing'),
    path('support/', views.support_view, name='support'),
    # URL pour l'admin Django
    path('admin/', admin.site.urls),
    path('', include('movies.urls')),
    # URLs pour l'API REST (endpoints JSON)
    path('', include('movies.urls')),
    path('api/users/', include('users.urls')),
    path('forgot-password/', TemplateView.as_view(template_name='forgot_password.html'), name='forgot_password'),
    path('reset-password/<str:token>/', TemplateView.as_view(template_name='reset_password.html'), name='reset_password'),
    path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile'),
    
    # URLs pour la réinitialisation de mot de passe
    # path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    # path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    # path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    # path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
]

# Servir les fichiers statiques et média en développement
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)