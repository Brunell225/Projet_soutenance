import pytest
from accounts.models import User


@pytest.mark.django_db
def test_create_user_with_required_fields():
    user = User.objects.create_user(
        username="user1",
        email="user1@example.com",
        password="TestPass123",
        company_name="Entreprise A",
        whatsapp_number="+2250102030405"
    )
    assert user.username == "user1"
    assert user.email == "user1@example.com"
    assert user.company_name == "Entreprise A"
    assert user.whatsapp_number == "+2250102030405"
    assert not user.is_superuser
    assert not user.is_platform_admin
