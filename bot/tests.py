from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from bot.models import BotResponse, BotSession, BotMessageHistory, Product


class BotTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="vendeur",
            email="vendeur@example.com",
            password="motdepasse123",
            whatsapp_number="+2250102030405",
            company_name="Shop 1",
            whatsapp_api_token="fake-token",
            phone_number_id="123456789"
        )
        self.user.is_business_account = True
        self.user.save()

        self.client.force_authenticate(user=self.user)
        self.intent_url = reverse("botresponse-list")
        self.send_url = reverse("send_whatsapp_message")
        self.analyse_url = reverse("analyse_message")
        self.toggle_url = reverse("toggle_bot")
        self.stats_url = reverse("bot_stats")
        self.reco_url = reverse("bot_recommendation")

    def test_create_intent(self):
        data = {
            "intent": "bonjour",
            "response": "Salut ! Comment puis-je vous aider ?",
            "is_question": False
        }
        response = self.client.post(self.intent_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_toggle_bot_status(self):
        data = {
            "client_number": "+2250123456789",
            "status": False
        }
        response = self.client.post(self.toggle_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session = BotSession.objects.get(user=self.user, client_number="+2250123456789")
        self.assertFalse(session.bot_actif)

    def test_send_message_fail(self):
        response = self.client.post(self.send_url, {"to": "+2250123456789"})
        self.assertIn(response.status_code, [200, 500])

    def test_analyse_message_no_match(self):
        BotResponse.objects.create(user=self.user, intent="commande", response="Vous souhaitez commander ?", is_question=False)
        payload = {"message": "aucune intention", "client_number": "+2250123456789"}
        response = self.client.post(self.analyse_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("bot_response", response.data)

    def test_bot_stats(self):
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_messages", response.data)

    def test_bot_recommendation(self):
        BotResponse.objects.create(user=self.user, intent="infos", response="Voici les infos", is_question=False)
        BotMessageHistory.objects.create(
            user=self.user,
            client_number="+2250123456789",
            client_message="infos",
            bot_response="Voici les infos"
        )
        response = self.client.get(self.reco_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("suggestion", response.data)


class BotEndToEndTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="e2euser",
            email="e2e@example.com",
            password="motdepasse123",
            whatsapp_number="+2250555667788",
            company_name="E2E Co",
            whatsapp_api_token="fake-token",
            phone_number_id="123456789"
        )
        self.user.is_business_account = True
        self.user.save()
        self.client.force_authenticate(user=self.user)

        self.intent_url = reverse("botresponse-list")
        self.analyse_url = reverse("analyse_message")

        # Création d'une intention liée à un produit
        self.intent = BotResponse.objects.create(
            user=self.user,
            intent="chaussures",
            response="Vous cherchez des chaussures ? Voici ce que nous avons.",
            question="Quel type de chaussures souhaitez-vous ?",
            is_question=True
        )

        Product.objects.create(
            user=self.user,
            name="Baskets Nike",
            description="Confortables et stylées",
            price=45000,
            is_available=True,
            tags="chaussures, sport"
        )

    def test_client_ask_for_product_and_get_bot_response(self):
        payload = {
            "client_number": "+2250777888999",
            "message": "je cherche des chaussures"
        }
        response = self.client.post(self.analyse_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("bot_response", response.data)
        self.assertIn("chaussures", response.data["bot_response"].lower())

        history = BotMessageHistory.objects.filter(user=self.user, client_number=payload["client_number"])
        self.assertTrue(history.exists())

    def test_client_answer_to_followup_question(self):
        # Étape 1 : le bot pose une question
        payload1 = {
            "client_number": "+2250777888999",
            "message": "je cherche des chaussures"
        }
        self.client.post(self.analyse_url, payload1)

        # Étape 2 : le client répond à la question
        payload2 = {
            "client_number": "+2250777888999",
            "message": "je veux des chaussures de sport"
        }
        response = self.client.post(self.analyse_url, payload2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("merci", response.data["bot_response"].lower())

        # Vérification de l’historique
        history = BotMessageHistory.objects.filter(
            user=self.user,
            client_number=payload2["client_number"]
        ).order_by('-timestamp')

        self.assertGreaterEqual(history.count(), 2)
        self.assertIn("sport", history.first().client_message.lower())
