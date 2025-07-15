from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé pour intégrer les infos WhatsApp Business API
    et les rôles spécifiques à la plateforme.
    """
    is_business_account = models.BooleanField(default=False)
    whatsapp_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    company_name = models.CharField(max_length=255)

    # Informations pour l’API WhatsApp
    whatsapp_api_token = models.TextField(blank=True, null=True)
    phone_number_id = models.CharField(max_length=100, blank=True, null=True)
    business_id = models.CharField(max_length=100, blank=True, null=True)

    # Suivi de l’état du compte
    has_completed_tutorial = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Rôle spécifique à la plateforme
    is_platform_admin = models.BooleanField(default=False)
    bot_enabled = models.BooleanField(default=True, help_text="Activer ou désactiver le bot pour ce vendeur")


    def __str__(self):
        return f"{self.company_name} ({self.whatsapp_number})"

class PasswordResetCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=15)

    def __str__(self):
        return f"{self.email} - {self.code}"