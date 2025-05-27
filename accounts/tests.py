from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from accounts.models import PasswordResetCode
from django.utils import timezone
from datetime import timedelta


class AccountsTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.profile_url = reverse('update_profile')
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "company_name": "Test Company",
            "whatsapp_number": "+2250102030405",
            "password": "strongpassword123",
            "password2": "strongpassword123"
        }

    def test_user_registration(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="testuser").exists())

    def test_authenticated_profile_access(self):
        self.client.post(self.register_url, self.user_data)
        user = User.objects.get(username="testuser")
        self.client.force_authenticate(user=user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AccountsValidationTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')

    def test_password_mismatch(self):
        data = {
            "username": "baduser",
            "email": "bad@example.com",
            "company_name": "Bad Co",
            "whatsapp_number": "+2250111222333",
            "password": "12345678",
            "password2": "87654321"
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_invalid_whatsapp_number(self):
        data = {
            "username": "baduser2",
            "email": "bad2@example.com",
            "company_name": "Bad Co 2",
            "whatsapp_number": "002250111222333",
            "password": "12345678",
            "password2": "12345678"
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("whatsapp_number", response.data)

    def test_duplicate_whatsapp_number(self):
        User.objects.create_user(
            username="original",
            email="o@example.com",
            password="12345678",
            whatsapp_number="+2250111222333",
            company_name="Original"
        )
        data = {
            "username": "duplicate",
            "email": "d@example.com",
            "company_name": "Duplicate",
            "whatsapp_number": "+2250111222333",
            "password": "12345678",
            "password2": "12345678"
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AccountsPermissionTests(APITestCase):
    def setUp(self):
        self.vendeur = User.objects.create_user(
            username="vendeur",
            email="vendeur@example.com",
            password="motdepasse123",
            whatsapp_number="+2250111222000",
            company_name="Shop V",
        )
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin1234",
            whatsapp_number="+2250111222001",
            company_name="Admin Co",
            is_platform_admin=True
        )
        self.superadmin = User.objects.create_superuser(
            username="superadmin",
            email="superadmin@example.com",
            password="superadmin123",
            whatsapp_number="+2250111222002",
            company_name="Super Admin Inc"
        )
        self.urls = {
            "vendeur": reverse('vendeur_only'),
            "admin": reverse('platform_admin'),
            "superadmin": reverse('superadmin')
        }

    def test_vendeur_access(self):
        self.client.force_authenticate(user=self.vendeur)
        self.assertEqual(self.client.get(self.urls["vendeur"]).status_code, 200)
        self.assertEqual(self.client.get(self.urls["admin"]).status_code, 403)
        self.assertEqual(self.client.get(self.urls["superadmin"]).status_code, 403)

    def test_platform_admin_access(self):
        self.client.force_authenticate(user=self.admin)
        self.assertEqual(self.client.get(self.urls["admin"]).status_code, 200)
        self.assertEqual(self.client.get(self.urls["vendeur"]).status_code, 403)
        self.assertEqual(self.client.get(self.urls["superadmin"]).status_code, 403)

    def test_superadmin_access(self):
        self.client.force_authenticate(user=self.superadmin)
        self.assertEqual(self.client.get(self.urls["superadmin"]).status_code, 200)
        self.assertEqual(self.client.get(self.urls["admin"]).status_code, 403)
        self.assertEqual(self.client.get(self.urls["vendeur"]).status_code, 403)

class PasswordResetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password="initialpassword",
            whatsapp_number="+2250700000000",
            company_name="Reset Co"
        )
        self.request_reset_url = reverse('request-password-reset')
        self.reset_confirm_url = reverse('reset-password-confirm')

    def test_request_password_reset_code_success(self):
        data = {"email": "reset@example.com"}
        response = self.client.post(self.request_reset_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PasswordResetCode.objects.filter(email="reset@example.com").exists())

    def test_request_password_reset_code_invalid_email(self):
        data = {"email": "notfound@example.com"}
        response = self.client.post(self.request_reset_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reset_password_with_valid_code(self):
        # Simuler l'envoi d'un code
        reset_code = PasswordResetCode.objects.create(email="reset@example.com", code="123456")

        data = {
            "email": "reset@example.com",
            "code": "123456",
            "new_password": "newstrongpassword"
        }
        response = self.client.post(self.reset_confirm_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifie que le mot de passe a été changé
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newstrongpassword"))

    def test_reset_password_with_invalid_code(self):
        data = {
            "email": "reset@example.com",
            "code": "wrongcode",
            "new_password": "newstrongpassword"
        }
        response = self.client.post(self.reset_confirm_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_password_with_expired_code(self):
        # Simuler un code expiré
        old_code = PasswordResetCode.objects.create(
            email="reset@example.com",
            code="999999",
            created_at=timezone.now() - timedelta(minutes=20)  # Code vieux de 20 min
        )

        data = {
            "email": "reset@example.com",
            "code": "999999",
            "new_password": "newstrongpassword"
        }
        response = self.client.post(self.reset_confirm_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)