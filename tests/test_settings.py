# tests/test_settings.py
import os
import pytest
from django.conf import settings
import django
django.setup()



def test_installed_apps():
    assert "accounts" in settings.INSTALLED_APPS, "'accounts' doit être dans INSTALLED_APPS"
    assert "bot" in settings.INSTALLED_APPS, "'bot' doit être dans INSTALLED_APPS"
    assert "rest_framework" in settings.INSTALLED_APPS, "'rest_framework' doit être dans INSTALLED_APPS"

def test_database_settings():
    db = settings.DATABASES["default"]
    assert db["ENGINE"] == "django.db.backends.postgresql", "La base doit utiliser PostgreSQL"
    assert db["NAME"] == "whatsapp_saas", "Nom de la base incorrect"
    assert db["USER"] == "postgres", "Utilisateur incorrect"
    assert db["PORT"] == "5432", "Port incorrect"

def test_custom_user_model():
    assert settings.AUTH_USER_MODEL == "accounts.User", "Le modèle utilisateur personnalisé doit être 'accounts.User'"

def test_jwt_authentication_class():
    auth_classes = settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]
    assert "rest_framework_simplejwt.authentication.JWTAuthentication" in auth_classes, "JWT Authentication doit être activé"
