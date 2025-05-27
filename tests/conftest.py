import os
import django
from django.conf import settings
from rest_framework.authtoken.models import Token
from accounts.models import User as CustomUser
import pytest

def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    django.setup()

@pytest.fixture
def create_authenticated_user(db):
    user = CustomUser.objects.create_user(
        email="botuser@test.com",
        password="testpass123",
        whatsapp_api_token="abc123",
        phone_number_id="987654321",
        whatsapp_number="+2250102030405",
        company_name="Yam's Group"
    )
    token = Token.objects.create(user=user)
    return user, str(token)