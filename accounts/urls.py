from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterAPIView,
    UserUpdateAPIView,
    PlatformAdminView,
    SuperAdminView,
    VendeurOnlyView, RequestPasswordResetCode, ResetPasswordConfirm
)

urlpatterns = [
    # ✅ Inscription
    path('register/', RegisterAPIView.as_view(), name='register'),

    # ✅ Connexion (JWT)
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

    # ✅ Rafraîchissement du token
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ✅ Mise à jour du profil utilisateur
    path('profile/', UserUpdateAPIView.as_view(), name='update_profile'),

    # ✅ Zone réservée aux administrateurs de la plateforme
    path('admin-zone/', PlatformAdminView.as_view(), name='platform_admin'),

    # ✅ Zone réservée aux superutilisateurs Django
    path('superadmin-zone/', SuperAdminView.as_view(), name='superadmin'),

    # ✅ Zone réservée aux vendeurs uniquement
    path('vendeur-zone/', VendeurOnlyView.as_view(), name='vendeur_only'),
    path('request-password-reset/', RequestPasswordResetCode.as_view(), name='request-password-reset'),
    path('reset-password-confirm/', ResetPasswordConfirm.as_view(), name='reset-password-confirm'),
]
