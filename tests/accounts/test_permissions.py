import pytest
from rest_framework.test import APIRequestFactory
from accounts.permissions import IsPlatformAdmin, IsSuperAdmin, IsVendeur
from accounts.models import User


@pytest.fixture
def create_user(db):
    def _create_user(**kwargs):
        defaults = {
            "username": "testuser",
            "email": "test@example.com",
            "company_name": "Test Company",
            "whatsapp_number": "+2250101010101",
            "password": "TestPass123"
        }
        defaults.update(kwargs)
        user = User.objects.create_user(**defaults)
        return user
    return _create_user


@pytest.mark.django_db
def test_is_platform_admin_permission(create_user):
    user = create_user(is_platform_admin=True)
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = user

    permission = IsPlatformAdmin()
    assert permission.has_permission(request, None)


@pytest.mark.django_db
def test_is_super_admin_permission(create_user):
    user = create_user(is_superuser=True)
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = user

    permission = IsSuperAdmin()
    assert permission.has_permission(request, None)


@pytest.mark.django_db
def test_is_vendeur_permission(create_user):
    user = create_user()  # Ni superuser ni admin plateforme
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = user

    permission = IsVendeur()
    assert permission.has_permission(request, None)
