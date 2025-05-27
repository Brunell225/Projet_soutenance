from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, PasswordResetCode
from .serializers import (
    RegisterSerializer,
    UserUpdateSerializer,
    UserSerializer
)
from .permissions import (
    IsPlatformAdmin,
    IsSuperAdmin,
    IsVendeur
)

# ✅ Vue pour l’inscription avec access + refresh token
class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        user = serializer.instance
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": serializer.data,
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            },
            status=status.HTTP_201_CREATED
        )

# ✅ Vue mise à jour profil avec retour de "user"
class UserUpdateAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserUpdateSerializer

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(self.get_object())
        return Response({
            "message": "Voici vos informations",
            "user": serializer.data
        })

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({
            "message": "Profil mis à jour",
            "user": serializer.data
        }, status=status.HTTP_200_OK)

# ✅ Admin plateforme
class PlatformAdminView(APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        return Response({"message": "Bienvenue, admin de la plateforme !"})

# ✅ Super admin Django
class SuperAdminView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        return Response({"message": "Bienvenue, superutilisateur Django !"})

# ✅ Vendeur uniquement
class VendeurOnlyView(APIView):
    permission_classes = [IsVendeur]

    def get(self, request):
        return Response({
            "message": f"Bienvenue {request.user.company_name}, vous êtes reconnu comme vendeur ✅"
        })

# ✅ Envoi du code de réinitialisation
class RequestPasswordResetCode(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email requis.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        code = get_random_string(6, allowed_chars='0123456789')
        PasswordResetCode.objects.create(email=email, code=code)

        send_mail(
            'Votre code de réinitialisation',
            f'Votre code est : {code}',
            'noreply@example.com',
            [email],
            fail_silently=False,
        )

        return Response({'message': 'Code envoyé par email.'}, status=status.HTTP_200_OK)

# ✅ Réinitialisation mot de passe
class ResetPasswordConfirm(APIView):
    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        new_password = request.data.get('new_password')

        if not all([email, code, new_password]):
            return Response({'error': 'Tous les champs sont requis.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            reset_code = PasswordResetCode.objects.filter(email=email, code=code).latest('created_at')
        except PasswordResetCode.DoesNotExist:
            return Response({'error': 'Code invalide.'}, status=status.HTTP_400_BAD_REQUEST)

        if reset_code.is_expired():
            return Response({'error': 'Code expiré.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Mot de passe réinitialisé.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)
