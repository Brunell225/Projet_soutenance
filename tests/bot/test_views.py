import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from bot.models import BotResponse, Product

@pytest.mark.django_db
class TestBotViews:

    def setup_method(self):
        self.client = APIClient()

    def authenticate(self, create_authenticated_user):
        self.user, token = create_authenticated_user
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

    def test_send_bot_message(self, create_authenticated_user):
        self.authenticate(create_authenticated_user)
        url = reverse("send_bot_message")
        payload = {
            "message": "Bonjour !",
            "client_number": "+2250102030405"
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == 200
        assert response.data["status"] == "Message envoyé avec succès"

    def test_toggle_bot(self, create_authenticated_user):
        self.authenticate(create_authenticated_user)
        url = reverse("toggle_bot")
        response = self.client.post(url, {"is_active": True}, format="json")
        assert response.status_code == 200
        assert response.data["message"] == "Le bot a été activé avec succès"
        self.user.refresh_from_db()
        assert self.user.is_bot_active is True

    def test_analyse_message_intent_found(self, create_authenticated_user):
        self.authenticate(create_authenticated_user)
        BotResponse.objects.create(user=self.user, intent="commande", response="Voici comment commander.")
        url = reverse("analyse_message")
        payload = {
            "message": "Comment commander ?",
            "client_number": "+2250102030405"
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == 200
        assert "commander" in response.data["bot_response"].lower()

    def test_analyse_message_with_product_price(self, create_authenticated_user):
        self.authenticate(create_authenticated_user)
        Product.objects.create(
            user=self.user,
            name="Chaise",
            price=20000,
            tags="chaise, prix",
            image="chaise.jpg"
        )
        url = reverse("analyse_message")
        payload = {
            "message": "Quel est le prix de la chaise ?",
            "client_number": "+2250102030405"
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == 200
        assert "20000" in response.data["bot_response"]

    def test_analyse_message_no_intent(self, create_authenticated_user):
        self.authenticate(create_authenticated_user)
        url = reverse("analyse_message")
        payload = {
            "message": "Blabla inconnue",
            "client_number": "+2250102030405"
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == 200
        assert "je suis désolé" in response.data["bot_response"].lower()

    def test_analyse_message_empty_input(self, create_authenticated_user):
        self.authenticate(create_authenticated_user)
        url = reverse("analyse_message")
        payload = {
            "message": "",
            "client_number": "+2250102030405"
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == 400
        assert "veuillez fournir" in response.data["error"].lower()
