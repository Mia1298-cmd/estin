from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView, UserDetailView,
    WatchlistViewSet, WatchHistoryViewSet, ForgotPasswordView,
    ResetPasswordView, ChangePasswordView, UpdateSubscriptionView
)
router = DefaultRouter()
router.register(r'watchlist', views.WatchlistViewSet, basename='watchlist')
router.register(r'history', views.WatchHistoryViewSet, basename='history')

urlpatterns = [
    # Endpoints API uniquement
    path('register/', views.RegisterView.as_view(), name='api-register'),
    path('login/', views.LoginView.as_view(), name='api-login'),
    path('logout/', views.LogoutView.as_view(), name='api-logout'),
    path('profile/', views.UserDetailView.as_view(), name='api-user-detail'),
    path('', include(router.urls)),
    path('forgot-password/', ForgotPasswordView.as_view(), name='api_forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='api_reset_password'),
    path('change-password/', ChangePasswordView.as_view(), name='api_change_password'),
    path('subscription/', UpdateSubscriptionView.as_view(), name='api_update_subscription'),
]