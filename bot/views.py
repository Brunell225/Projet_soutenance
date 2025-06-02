from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view 
from rest_framework import viewsets, permissions, generics
from django.utils.timezone import now, timedelta
from django.views.decorators.csrf import csrf_exempt
import json
from .whatsapp_api import send_message_to_whatsapp
from django.http import HttpResponse
from django.db.models import Count, Q
from .serializers import BotResponseSerializer, BotMessageHistorySerializer, ProductSerializer
from .models import BotResponse, BotMessageHistory, BotSession, Product
from .nlp_utils import detect_intention_spacy, extract_keywords
from accounts.permissions import IsVendeur
import requests
import re
from accounts.models import User
import json
import logging

logger = logging.getLogger(__name__)


VERIFY_TOKEN = 'molly_bot_verify' 

# ✅ ✅ Envoi d’un template (à configurer côté Meta)
class SendBotMessageAPIView(APIView):
    permission_classes = [IsAuthenticated, IsVendeur]

    def post(self, request):
        user = request.user
        to_number = request.data.get("to") or user.whatsapp_number

        if not all([user.whatsapp_api_token, user.phone_number_id, to_number]):
            return Response({"error": "Les informations WhatsApp sont incomplètes."}, status=400)

        headers = {
            "Authorization": f"Bearer {user.whatsapp_api_token}",
            "Content-Type": "application/json"
        }

        data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": "hello_world",
                "language": { "code": "en_US" }
            }
        }

        url = f"https://graph.facebook.com/v18.0/{user.phone_number_id}/messages"

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
        except requests.RequestException as e:
            return Response({"error": f"Erreur lors de l’envoi du message : {str(e)}"}, status=500)

        return Response({"status": f"Message envoyé à {to_number}"})


# ✅ ✅ IA conversationnelle (analyse + réponse + produits)
class AnalyseMessageView(APIView):
    permission_classes = [IsAuthenticated, IsVendeur]

    def post(self, request):
        user = request.user
        message = request.data.get('message', '').lower()
        client_number = request.data.get('client_number')

        if not message or not client_number:
            return Response({"error": "Message ou numéro client manquant."}, status=400)

        session, _ = BotSession.objects.get_or_create(user=user, client_number=client_number)

        if not session.bot_actif:
            return Response({
                "status": "Bot désactivé pour ce client.",
                "client_number": client_number
            })

        response_text = ""
        product_suggestions = []

        # 🔍 Détection d’intention + confiance
        doc = detect_intention_spacy(message)
        intent = None
        confidence = 0.0

        if doc and hasattr(doc, "cats") and doc.cats:
            intent = max(doc.cats, key=doc.cats.get)
            confidence = doc.cats[intent]
            print(f"🔍 Intention détectée : {intent} ({confidence * 100:.2f}%)")
            if confidence < 0.3:
                intent = None
                print("⚠️ Confiance trop faible, on ignore l'intention.")
        else:
            print("❌ Aucun intent détecté")

        if session.current_intent and session.last_question:
            response_text = f"Merci pour l’info concernant {session.current_intent} 👍"
            session.current_intent = None
            session.last_question = None
            session.save()

        else:
            matched = BotResponse.objects.filter(user=user, intent__iexact=intent) if intent else []

            if matched:
                parts = [f"- {r.response}" for r in matched]
                questions = [f"\n❓ {r.question}" for r in matched if r.is_question and r.question]
                response_text = "🤖 Voici ce que j’ai compris :\n" + "\n".join(parts) + "".join(questions)

                if matched[0].is_question and matched[0].question:
                    session.current_intent = matched[0].intent
                    session.last_question = matched[0].question
                    session.save()

                # 🔍 Recherche de produits par mots-clés
                keywords = extract_keywords(message)
                filters = Q(user=user, is_available=True)
                for kw in keywords:
                    filters &= Q(tags__icontains=kw)

                product_suggestions = Product.objects.filter(filters)

            else:
                response_text = "Je n’ai pas bien compris. Pouvez-vous reformuler ?"

        # 📝 Historique enrichi
        BotMessageHistory.objects.create(
            user=user,
            client_number=client_number,
            client_message=message,
            bot_response=response_text,
            detected_intent=intent,
            confidence_score=confidence
        )

        # 📤 Envoi WhatsApp
        url = f"https://graph.facebook.com/v18.0/{user.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {user.whatsapp_api_token}",
            "Content-Type": "application/json"
        }

        data = {
            "messaging_product": "whatsapp",
            "to": client_number,
            "type": "text",
            "text": {"body": response_text}
        }

        try:
            whatsapp_response = requests.post(url, headers=headers, json=data)
            whatsapp_response.raise_for_status()
            whatsapp_result = whatsapp_response.json()
        except requests.RequestException as e:
            whatsapp_result = {"error": str(e)}
            response_text += "\n(Note : l’envoi WhatsApp a échoué)"

        # 📸 Envoi images produit
        for prod in product_suggestions[:3]:
            if prod.image and hasattr(prod.image, "url"):
                image_data = {
                    "messaging_product": "whatsapp",
                    "to": client_number,
                    "type": "image",
                    "image": {
                        "link": request.build_absolute_uri(prod.image.url),
                        "caption": f"{prod.name}\nPrix : {prod.price} FCFA"
                    }
                }
                try:
                    requests.post(url, headers=headers, json=image_data)
                except requests.RequestException:
                    continue

        return Response({
            "bot_response": response_text,
            "whatsapp_response": whatsapp_result
        })



# ✅ CRUD Intentions
class BotResponseViewSet(viewsets.ModelViewSet):
    serializer_class = BotResponseSerializer
    permission_classes = [IsAuthenticated, IsVendeur]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return BotResponse.objects.none()
        return BotResponse.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



# ✅ Historique messages
class MessageHistoryListView(generics.ListAPIView):
    serializer_class = BotMessageHistorySerializer
    permission_classes = [IsAuthenticated, IsVendeur]

    def get_queryset(self):
        user = self.request.user
        client_number = self.request.query_params.get('client_number')
        if client_number:
            return BotMessageHistory.objects.filter(user=user, client_number=client_number).order_by('-timestamp')
        return BotMessageHistory.objects.none()


# ✅ Activation / désactivation du bot par client
@api_view(['POST'])
def toggle_bot(request):
    client_number = request.data.get('client_number')
    status = request.data.get('status')

    # Accepte aussi "true"/"false" en string
    if isinstance(status, str):
        status = status.lower() == 'true'

    if not client_number or not isinstance(status, bool):
        return Response({"error": "Données invalides : 'client_number' ou 'status' (booléen) manquant."}, status=400)

    session, _ = BotSession.objects.get_or_create(
        user=request.user,
        client_number=client_number
    )
    session.bot_actif = status
    session.save()

    return Response({
        "status": "activé" if status else "désactivé",
        "client": client_number
    })


# ✅ Statistiques bot (filtrables)
class BotStatsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsVendeur]

    def get(self, request):
        user = request.user
        period = request.query_params.get('period', 'all')
        messages = BotMessageHistory.objects.filter(user=user)

        today = now().date()
        if period == "today":
            messages = messages.filter(timestamp__date=today)
        elif period == "week":
            messages = messages.filter(timestamp__date__gte=today - timedelta(days=7))
        elif period == "month":
            messages = messages.filter(timestamp__date__gte=today - timedelta(days=30))

        total_messages = messages.count()
        clients_uniques = messages.values('client_number').distinct().count()
        intentions = BotResponse.objects.filter(user=user)

        intent_counts = {
            intent.intent: messages.filter(bot_response__icontains=intent.response[:20]).count()
            for intent in intentions
        }

        non_compris = messages.filter(bot_response__icontains="je n’ai pas bien compris").count()
        comprehension = round(100 - ((non_compris / total_messages) * 100), 2) if total_messages else 0

        return Response({
            "période": period,
            "total_messages": total_messages,
            "clients_uniques": clients_uniques,
            "intentions_detectées": intent_counts,
            "non_compris": non_compris,
            "taux_de_compréhension": f"{comprehension} %"
        })


# ✅ Recommandations IA
class BotRecommendationAPIView(APIView):
    permission_classes = [IsAuthenticated, IsVendeur]

    def get(self, request):
        user = request.user
        messages = BotMessageHistory.objects.filter(user=user)
        intentions = BotResponse.objects.filter(user=user)

        max_intent = None
        max_count = 0

        for intent in intentions:
            count = messages.filter(bot_response__icontains=intent.response[:20]).count()
            if count > max_count:
                max_count = count
                max_intent = intent.intent

        suggestion = f"Vos clients demandent souvent '{max_intent}'. Ajoutez plus de réponses ou de produits liés à cette intention." if max_intent else "Aucune recommandation pour le moment."

        return Response({
            "intention_forte": max_intent,
            "nombre_demandes": max_count,
            "suggestion": suggestion
        })

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsVendeur]

    def get_queryset(self):
        user = self.request.user
        queryset = Product.objects.filter(user=user, is_available=True)

        tag_filter = self.request.query_params.get('tag')
        if tag_filter:
            tags = [t.strip() for t in tag_filter.split(',')]
            for tag in tags:
                queryset = queryset.filter(tags__icontains=tag)

        return queryset.order_by('-id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@csrf_exempt
def webhook_view(request):
    if request.method == 'GET':
        mode = request.GET.get('hub.mode')
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        if mode == 'subscribe' and verify_token == VERIFY_TOKEN:
            print("✅ Webhook vérifié par Meta")
            return HttpResponse(challenge)
        print("❌ Tentative de vérification échouée")
        return HttpResponse("Token invalide ou mode incorrect", status=403)

    elif request.method == 'POST':
        print("🚨 Webhook POST reçu !")  # 🔥 Important pour confirmer l'appel
        try:
            data = json.loads(request.body.decode('utf-8'))
            print("📨 Données reçues :", json.dumps(data, indent=2))

            for ent in data.get('entry', []):
                for change in ent.get('changes', []):
                    value = change.get('value', {})
                    messages = value.get('messages', [])
                    metadata = value.get('metadata', {})
                    phone_number_id = metadata.get("phone_number_id") or metadata.get("display_phone_number")

                    print("📞 Phone ID reçu :", phone_number_id)

                    if not messages:
                        print("📭 Aucun message reçu dans cette requête.")
                        continue

                    msg = messages[0]
                    from_number = msg.get('from')
                    message_text = msg.get('text', {}).get('body', '')

                    print(f"💬 Message reçu de {from_number} : '{message_text}'")

                    # Analyse NLP
                    try:
                        doc = detect_intention_spacy(message_text)
                        intent = doc.cats if hasattr(doc, "cats") else {}
                        print("🤖 Intention NLP :", intent)
                    except Exception as e:
                        print("⚠️ Erreur NLP :", str(e))
                        intent = {}

                    if intent:
                        best_intent = max(intent, key=intent.get)
                        confidence = intent[best_intent]
                        response = f"Tu parles de : {best_intent} ! Je peux t’aider 👍🏽" if confidence > 0.6 else "Je ne suis pas sûr d’avoir compris. Peux-tu reformuler ?"
                    else:
                        response = "Je n’ai pas compris ton message."

                    # Trouver le vendeur lié à ce numéro
                    vendeur = User.objects.filter(
                        is_business_account=True,
                        whatsapp_api_token__isnull=False,
                        phone_number_id=phone_number_id
                    ).first()

                    if vendeur:
                        try:
                            print("📤 Envoi du message à WhatsApp...")
                            send_message_to_whatsapp(from_number, response, vendeur)
                            print("✅ Message WhatsApp envoyé avec succès.")
                        except Exception as send_err:
                            print("❌ Erreur lors de l'envoi :", send_err)
                    else:
                        print("❌ Aucun vendeur trouvé pour ce phone_number_id :", phone_number_id)

        except Exception as global_err:
            print("🚨 Erreur globale webhook :", global_err)
            return HttpResponse("Erreur interne", status=500)

        return HttpResponse("EVENT_RECEIVED", status=200)

    return HttpResponse("Méthode non autorisée", status=405)