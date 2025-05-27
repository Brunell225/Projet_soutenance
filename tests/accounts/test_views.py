import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from accounts.models import User


@pytest.mark.django_db
def test_user_registration():
    client = APIClient()
    url = reverse('register')
    data = {
        "username": "newuser",
        "email": "new@example.com",
        "company_name": "Ma société",
        "whatsapp_number": "+2250708091011",
        "password": "StrongPass123!",
        "password2": "StrongPass123!"
    }
    response = client.post(url, data, format='json')
    assert response.status_code == 201
    assert response.data["username"] == "newuser"


@pytest.mark.django_db
def test_user_profile_update():
    user = User.objects.create_user(
        username="profileuser",
        email="profile@example.com",
        company_name="Test Update",
        whatsapp_number="+2250606060606",
        password="ProfilePass123"
    )

    client = APIClient()
    client.force_authenticate(user=user)
    url = reverse('update_profile')
    data = {
        "company_name": "Entreprise Modifiée",
        "whatsapp_api_token": "nouveau_token_123"
    }
    response = client.patch(url, data, format='json')
    assert response.status_code == 200
    assert response.data["company_name"] == "Entreprise Modifiée"


@pytest.mark.django_db
def test_platform_admin_access():
    admin = User.objects.create_user(
        username="adminuser",
        email="admin@example.com",
        company_name="AdminCorp",
        whatsapp_number="+2250505050505",
        password="AdminPass123",
        is_platform_admin=True
    )
    client = APIClient()
    client.force_authenticate(user=admin)
    url = reverse('platform_admin')
    response = client.get(url)
    assert response.status_code == 200
    assert "Bienvenue, admin de la plateforme" in response.data["message"]


@pytest.mark.django_db
def test_superadmin_access():
    superadmin = User.objects.create_superuser(
        username="superadmin",
        email="super@example.com",
        password="SuperPass123",
        company_name="SuperInc",
        whatsapp_number="+2250404040404"
    )
    client = APIClient()
    client.force_authenticate(user=superadmin)
    url = reverse('superadmin')
    response = client.get(url)
    assert response.status_code == 200
    assert "Bienvenue, superutilisateur Django" in response.data["message"]


@pytest.mark.django_db
def test_vendeur_access():
    vendeur = User.objects.create_user(
        username="vendeuruser",
        email="vendeur@example.com",
        company_name="VentePro",
        whatsapp_number="+2250303030303",
        password="VendeurPass123"
    )
    client = APIClient()
    client.force_authenticate(user=vendeur)
    url = reverse('vendeur_only')
    response = client.get(url)
    assert response.status_code == 200
    assert "vous êtes reconnu comme vendeur" in response.data["message"]

@pytest.mark.django_db
def test_jwt_login():
    user = User.objects.create_user(
        username="jwtuser",
        email="jwt@example.com",
        password="TestPass123",
        company_name="JWT Corp",
        whatsapp_number="+22501020304"
    )
    client = APIClient()
    response = client.post('/api/accounts/login/', {
        "username": "jwtuser",
        "password": "TestPass123"
    }, format='json')
    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data