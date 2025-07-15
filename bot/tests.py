# bot/tests.py

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock
from bot.models import Product, BotResponse

User = get_user_model()


# === UTILITAIRE POUR MOCK WHATSAPP API ===
def mock_whatsapp_success(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"status": "sent"}


# === TESTS UNITAIRES ===
@pytest.mark.unit
class BotModelTests(APITestCase):
    def test_bot_response_str(self):
        user = User.objects.create_user(username="test_user")
        br = BotResponse.objects.create(user=user, intent="salutation", response="Bonjour !")
        self.assertEqual(str(br), "salutation → Bonjour !...")

    def test_product_str(self):
        user = User.objects.create_user(username="test_user2", company_name="TIR-CI")
        p = Product.objects.create(user=user, name="Robe AI", price=10000, tags="robe,ai")
        expected = f"Robe AI - {user.company_name}"
        self.assertEqual(str(p), expected)


# === TESTS D’INTÉGRATION ===
@pytest.mark.integration
class BotIntegrationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="integration_user",
            password="testpass",
            company_name="TIR-CI",
            whatsapp_api_token="test_token",
            phone_number_id="123"
        )
        self.client.force_authenticate(user=self.user)

    def test_detect_intention_produit(self):
        BotResponse.objects.create(
            user=self.user,
            intent="produit",
            response="Voici nos articles disponibles :",
            is_question=False
        )
        Product.objects.create(
            user=self.user,
            name="Robe Africaine",
            price=12000,
            tags="robe,africain",
            is_available=True
        )

        url = reverse("analyse_message")
        data = {"message": "je cherche une robe", "client_number": "22998765432"}

        with patch("requests.post") as mocked_post, \
             patch("bot.views.detect_intention_spacy") as mock_detect:

            mock_doc = MagicMock()
            mock_doc.cats = {"produit": 0.9}
            mock_detect.return_value = mock_doc

            mock_whatsapp_success(mocked_post)

            response = self.client.post(url, data)
            self.assertEqual(response.status_code, 200)
            self.assertIn("articles disponibles", response.data["bot_response"])


# === TESTS END-TO-END ===
@pytest.mark.e2e
class BotEndToEndTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="e2e_user",
            password="testpass",
            company_name="TIR-CI",
            whatsapp_api_token="test_token",
            phone_number_id="123"
        )
        self.client.force_authenticate(user=self.user)

    def test_client_conversation_flow(self):
        BotResponse.objects.create(
            user=self.user,
            intent="commande",
            response="Souhaitez-vous commander ?",
            is_question=True,
            question="Quel article voulez-vous ?"
        )
        Product.objects.create(
            user=self.user,
            name="Jean slim",
            price=15000,
            tags="jean,slim",
            is_available=True
        )

        url = reverse("analyse_message")
        data1 = {"message": "je veux commander", "client_number": "22501020304"}
        data2 = {"message": "jean slim bleu", "client_number": "22501020304"}

        with patch("requests.post") as mocked_post, \
             patch("bot.views.detect_intention_spacy") as mock_detect:

            mock_doc = MagicMock()
            mock_doc.cats = {"commande": 0.9}
            mock_detect.return_value = mock_doc

            mock_whatsapp_success(mocked_post)

            res1 = self.client.post(url, data1)
            self.assertEqual(res1.status_code, 200)
            self.assertIn("souhaitez-vous commander", res1.data["bot_response"].lower())

            res2 = self.client.post(url, data2)
            self.assertEqual(res2.status_code, 200)
            self.assertIn("merci", res2.data["bot_response"].lower())

    def test_intention_non_comprise(self):
        url = reverse("analyse_message")
        data = {"message": "qwerty azerty", "client_number": "22911122233"}

        with patch("requests.post") as mocked_post, \
             patch("bot.views.detect_intention_spacy") as mock_detect:

            mock_doc = MagicMock()
            mock_doc.cats = {"salutation": 0.1}
            mock_detect.return_value = mock_doc

            mock_whatsapp_success(mocked_post)

            response = self.client.post(url, data)
            self.assertEqual(response.status_code, 200)
            self.assertIn("je n’ai pas bien compris", response.data["bot_response"].lower())
