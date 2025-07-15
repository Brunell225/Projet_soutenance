import random
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes 
from rest_framework import viewsets, permissions, generics
from rest_framework.generics import RetrieveAPIView
from django.utils.timezone import now, timedelta
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import MultiPartParser, FormParser
import json
from bot.intent_router import detect_intent_pipeline, generate_reply
from .escalation import handle_escalation
from .intent_engine import route_intent
from bot.config.nlp_settings import NLP_CONFIG
from .whatsapp_api import send_message_to_whatsapp
from django.http import HttpResponse
from django.db.models import Count, Q
from .serializers import BotResponseSerializer, BotMessageHistorySerializer, ProductSerializer, ProductDetailSerializer
from .models import BotResponse, BotMessageHistory, BotSession, Product
from .nlp_utils import detect_intention, extract_keywords, search_products
from accounts.permissions import IsVendeur
import requests
import re
from accounts.models import User
import logging

logger = logging.getLogger(__name__)


VERIFY_TOKEN = 'molly_bot_verify' 

#  Envoi d’un template (à configurer côté Meta)
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


# IA conversationnelle (analyse + réponse + produits)
#from rest_framework.permissions import IsAuthenticated
#from rest_framework.views import APIView
#from rest_framework.response import Response
#from django.db.models import Q
#from .models import BotSession, BotResponse, BotMessageHistory, Product
#from .nlp_utils import detect_intention_spacy, extract_keywords
#from accounts.permissions import IsVendeur
#from django.utils.timezone import now, timedelta
#import requests


def is_simulation_number(number):
    return number.startswith("simu") or number.startswith("test") or number.endswith("0000")


class AnalyseMessageView(APIView):
    permission_classes = [IsAuthenticated, IsVendeur]

    def post(self, request):
        user = request.user
        if not user.bot_enabled:
            return Response({
                "status": "bot_disabled",
                "message": "Le bot est désactivé pour ce vendeur."
            }, status=403)

        message = request.data.get("message", "").strip()
        client_number = request.data.get("client_number")
        if not message or not client_number:
            return Response({"error": "Message ou numéro client manquant."}, status=400)

        is_simulation = is_simulation_number(client_number)
        request.is_simulation = is_simulation

        session, _ = BotSession.objects.get_or_create(
            user=user,
            client_number=client_number,
            defaults={"bot_actif": True, "current_intent": None, "last_question": None}
        )

        if self._check_silence_mode(session):
            return Response({
                "status": "silence",
                "bot_response": None,
                "debug": request.is_simulation
            }, status=200)

        intent, confidence = detect_intention(message)
        self._log_detection(user, client_number, message, intent, confidence)

        if intent == "rejet":
            return self._handle_rejection(session, user, client_number, message, request)

        if not intent:
            return self._handle_unknown_message(session, user, client_number, message, request)

        return self._process_intent(session, user, client_number, message, intent, confidence, request)

    def _check_silence_mode(self, session):
        silence_until = getattr(session, "bot_silence_until", None)
        return silence_until and silence_until > now()

    def _log_detection(self, user, client_number, message, intent, confidence):
        print(
            f"\n NLP Detection - User: {user.id} | Client: {client_number}\n"
            f"Message: '{message}'\n"
            f"Intent: {intent} | Confidence: {confidence:.2f}\n"
            f"Timestamp: {now()}\n"
        )

    def _handle_rejection(self, session, user, client_number, message, request):
        response_text = "Pas de souci . Je reste disponible si besoin !"
        session.bot_silence_until = now() + timedelta(minutes=15)
        session.save()

        self._save_history_and_respond(user, client_number, message, response_text, "rejet", 1.0, request)

        return Response({
            "bot_response": response_text,
            "detected_intent": "rejet",
            "confidence": 1.0,
            "debug": request.is_simulation
        })

    def _handle_unknown_message(self, session, user, client_number, message, request):
        keywords = extract_keywords(message)
        guessed_intent = self._guess_intent_from_keywords(keywords)

        if guessed_intent:
            response_text = self._get_guided_response(guessed_intent, keywords)
        else:
            response_text = random.choice(NLP_CONFIG["FALLBACK_RESPONSES"])
            if any(trigger in message.lower() for trigger in NLP_CONFIG["KEYWORD_TRIGGERS"]["urgence"]):
                response_text += "\n\n(Si c'est urgent, tapez 'URGENT' pour parler à un conseiller)"

        self._save_history_and_respond(user, client_number, message, response_text, None, 0.0, request)

        return Response({
            "bot_response": response_text,
            "detected_intent": None,
            "confidence": 0.0,
            "debug": request.is_simulation
        })

    def _guess_intent_from_keywords(self, keywords):
        keyword_to_intent = {
            "livraison": "livraison",
            "paiement": "paiement",
            "commander": "commande",
            "retour": "retour",
            "horaire": "horaire",
            "salutation": "salutation"
        }
        for kw in keywords:
            for trigger, intent in keyword_to_intent.items():
                if trigger in kw:
                    return intent
        return None

    def _get_guided_response(self, intent, keywords):
        base_responses = {
            "livraison": "À propos de la livraison, quelle est votre question précise concernant {} ?",
            "paiement": "Pour le paiement {}, que souhaitez-vous savoir ?",
            "commande": "Vous voulez commander {}. Quel article précisément ?",
            "retour": "Pour le retour {}, avez-vous besoin d'aide ?",
            "horaire": "Nos horaires pour {} sont-ils ce que vous cherchez ?"
        }
        keyword_str = ", ".join(keywords[:3]) if keywords else "cette question"
        return base_responses.get(intent, "Pouvez-vous préciser ?").format(keyword_str)

    def _process_intent(self, session, user, client_number, message, intent, confidence, request):
        if session.current_intent and session.last_question:
            return self._handle_follow_up(session, user, client_number, message, request)

        matched_responses = BotResponse.objects.filter(user=user, intent__iexact=intent)
        if matched_responses.exists():
            return self._handle_configured_response(session, user, client_number, message, intent, confidence, matched_responses, request)

        return self._handle_default_response(session, user, client_number, message, intent, confidence, request)

    def _handle_follow_up(self, session, user, client_number, message, request):
        keywords = extract_keywords(message)
        products = search_products(user, message)

        if products:
            product_names = ", ".join(p.name for p in products[:3])
            response_text = f"Merci pour ces précisions ! Voici ce que j'ai trouvé :\n{product_names}\nVoulez-vous plus d'informations sur l'un d'eux ?"
        else:
            response_text = "Merci pour ces détails. Malheureusement je n'ai rien trouvé correspondant à votre demande. Souhaitez-vous reformuler ?"

        session.current_intent = None
        session.last_question = None
        session.save()

        self._save_history_and_respond(user, client_number, message, response_text, None, 0.9, request)
        self._send_product_images(user, client_number, products[:3], request)

        return Response({
            "bot_response": response_text,
            "detected_intent": None,
            "confidence": 0.9,
            "debug": request.is_simulation
        })

    def _handle_configured_response(self, session, user, client_number, message, intent, confidence, matched_responses, request):
        primary_response = matched_responses.first()
        response_text = primary_response.response

        if primary_response.is_question and primary_response.question:
            session.current_intent = intent
            session.last_question = primary_response.question
            session.save()
            response_text += f"\n\n{primary_response.question}"

        product_suggestions = search_products(user, message) if intent in ["produit", "commande"] else []
        self._save_history_and_respond(user, client_number, message, response_text, intent, confidence, request)
        self._send_product_images(user, client_number, product_suggestions[:3], request)

        return Response({
            "bot_response": response_text,
            "detected_intent": intent,
            "confidence": confidence,
            "debug": request.is_simulation
        })

    def _handle_default_response(self, session, user, client_number, message, intent, confidence, request):
        response_text = self._get_default_response(intent, message, user)
        product_suggestions = search_products(user, message) if intent in ["produit", "commande"] else []

        self._save_history_and_respond(user, client_number, message, response_text, intent, confidence, request)
        self._send_product_images(user, client_number, product_suggestions[:3], request)

        return Response({
            "bot_response": response_text,
            "detected_intent": intent,
            "confidence": confidence,
            "debug": request.is_simulation
        })

    def _get_default_response(self, intent, message, user):
        responses = {
            "salutation": ["Bonjour  ! Comment puis-je vous aider ?", "Salut ! Dites-moi ce dont vous avez besoin", "Bienvenue ! Que puis-je faire pour vous aujourd'hui ?"],
            "remerciement": ["Avec plaisir !  N'hésitez pas si vous avez d'autres questions.", "Merci à vous ! Revenez quand vous voulez.", "C'était un plaisir de vous aider !"],
            "commande": "Pour commander, veuillez préciser :\n- L'article\n- La taille/couleur\n- La quantité",
            "paiement": "Modes de paiement acceptés :\n- Mobile Money (Orange/Moov)\n- Carte bancaire\n- Espèces à la livraison",
            "livraison": "Livraison en 24-72h selon votre zone.\nFrais : 1000-3000 FCFA\nSuivi de colis disponible. Besoin de plus d'infos ?",
            "retour": "Politique de retour :\n- 7 jours pour changer d'avis\n- Produit neuf dans son emballage\nVoulez-vous initier un retour ?",
            "problème": "Désolé pour ce souci \nMerci de décrire le problème en détails pour que je puisse aider.",
            "horaire": "Horaires d'ouverture :\nLundi-Vendredi : 8h-19h\nSamedi : 9h-17h\nDimanche : Fermé",
            "produit": "Nous avons un large choix de produits !\nDites-moi ce que vous cherchez :\n- Type (robe, chaussures...)\n- Taille/Couleur\n- Budget approximatif"
        }
        return random.choice(responses.get(intent, NLP_CONFIG["FALLBACK_RESPONSES"])) if isinstance(responses.get(intent), list) else responses.get(intent, random.choice(NLP_CONFIG["FALLBACK_RESPONSES"]))

    def _save_history_and_respond(self, user, client_number, client_message, bot_response, intent, confidence, request):
        BotMessageHistory.objects.create(
            user=user,
            client_number=client_number,
            client_message=client_message,
            bot_response=bot_response,
            detected_intent=intent,
            confidence_score=confidence
        )
        self.send_whatsapp_message(user, client_number, bot_response, request)

    def _send_product_images(self, user, client_number, products, request):
        for product in products:
            if product.image and hasattr(product.image, "url"):
                self.send_whatsapp_image(user, client_number, product, request)

    def send_whatsapp_message(self, user, to_number, message, request):
        if getattr(request, "is_simulation", False):
            print(f"[SIMULATION] Message NON envoyé : {message}")
            return

        url = f"https://graph.facebook.com/v18.0/{user.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {user.whatsapp_api_token}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": message}
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=5)
            response.raise_for_status()
            print(f" Message WhatsApp envoyé à {to_number}")
        except requests.RequestException as e:
            print(f" Erreur WhatsApp : {str(e)}")

    def send_whatsapp_image(self, user, to_number, product, request):
        if getattr(request, "is_simulation", False):
            print(f"[SIMULATION] Image NON envoyée pour {product.name}")
            return

        if not product.image or not hasattr(product.image, "url"):
            return

        url = f"https://graph.facebook.com/v18.0/{user.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {user.whatsapp_api_token}",
            "Content-Type": "application/json"
        }
        image_payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "image",
            "image": {
                "link": request.build_absolute_uri(product.image.url),
                "caption": f"{product.name}\nPrix : {product.price} FCFA"
            }
        }

        try:
            response = requests.post(url, headers=headers, json=image_payload, timeout=5)
            response.raise_for_status()
            print(f" Image WhatsApp envoyée pour {product.name}")
        except requests.RequestException as e:
            print(f"Erreur image WhatsApp : {str(e)}")

# CRUD Intentions
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
        if period == "Jour":
            messages = messages.filter(timestamp__date=today)
        elif period == "Semaine":
            messages = messages.filter(timestamp__date__gte=today - timedelta(days=7))
        elif period == "Mois":
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


# Recommandations IA
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
    parser_classes = [MultiPartParser, FormParser]  # pour l'upload d'image

    def get_queryset(self):
        user = self.request.user
        queryset = Product.objects.filter(user=user)

        # Filtres dynamiques
        tag_filter = self.request.query_params.get('tag')
        if tag_filter:
            tags = [t.strip().lower() for t in tag_filter.split(',')]
            for tag in tags:
                queryset = queryset.filter(tags__icontains=tag)

        size_filter = self.request.query_params.get('size')
        if size_filter:
            queryset = queryset.filter(sizes__icontains=size_filter)

        color_filter = self.request.query_params.get('color')
        if color_filter:
            queryset = queryset.filter(colors__icontains=color_filter)

        available = self.request.query_params.get('available')
        if available is not None:
            if isinstance(available, str):
                available = available.lower() == "true"
            queryset = queryset.filter(is_available=available)

        return queryset.order_by('-id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@api_view(['GET'])
def get_product_filters(request):
    if not request.user.is_authenticated or not isinstance(request.user, User) or not request.user.is_vendeur:
        return Response({"detail": "Non autorisé."}, status=403)

    user = request.user
    products = Product.objects.filter(user=user, is_available=True)

    all_tags = set()
    all_sizes = set()
    all_colors = set()

    for p in products:
        all_tags.update(p.tags.lower().split(','))
        all_sizes.update(p.sizes)
        all_colors.update(p.colors)

    return Response({
        "tags": sorted(all_tags),
        "sizes": sorted(all_sizes),
        "colors": sorted(all_colors)
    })



@api_view(['GET'])
def bot_retrieve_products(request):
    if not request.user.is_authenticated or not isinstance(request.user, User) or not request.user.is_vendeur:
        return Response({"detail": "Non autorisé."}, status=403)

    user = request.user
    message = request.query_params.get("q", "")
    keywords = extract_keywords(message)

    if not keywords:
        return Response({"results": []})

    query = Q()
    for kw in keywords:
        query |= Q(name__icontains=kw)
        query |= Q(tags__icontains=kw)
        query |= Q(colors__icontains=kw)
        query |= Q(sizes__icontains=kw)

    products = Product.objects.filter(user=user, is_available=True).filter(query).distinct()[:5]
    serialized = ProductSerializer(products, many=True, context={"request": request})
    return Response({"results": serialized.data})





@csrf_exempt
def webhook_view(request):
    if request.method == 'GET':
        mode = request.GET.get('hub.mode')
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        if mode == 'subscribe' and verify_token == VERIFY_TOKEN:
            print(" Webhook vérifié par Meta")
            return HttpResponse(challenge)
        print(" Tentative de vérification échouée")
        return HttpResponse("Token invalide ou mode incorrect", status=403)

    elif request.method == 'POST':
        print(" Webhook POST reçu !")  # Important pour confirmer l'appel
        try:
            data = json.loads(request.body.decode('utf-8'))
            print(" Données reçues :", json.dumps(data, indent=2))

            for ent in data.get('entry', []):
                for change in ent.get('changes', []):
                    value = change.get('value', {})
                    messages = value.get('messages', [])
                    metadata = value.get('metadata', {})
                    phone_number_id = metadata.get("phone_number_id") or metadata.get("display_phone_number")

                    print(" Phone ID reçu :", phone_number_id)

                    if not messages:
                        print(" Aucun message reçu dans cette requête.")
                        continue

                    msg = messages[0]
                    from_number = msg.get('from')
                    message_text = msg.get('text', {}).get('body', '')

                    print(f" Message reçu de {from_number} : '{message_text}'")

                    # Analyse NLP
                    try:
                        doc = detect_intention(message_text)
                        intent = doc.cats if hasattr(doc, "cats") else {}
                        print(" Intention NLP :", intent)
                    except Exception as e:
                        print(" Erreur NLP :", str(e))
                        intent = {}

                    if intent:
                        best_intent = max(intent, key=intent.get)
                        confidence = intent[best_intent]
                        response = f"Tu parles de : {best_intent} ! Je peux t’aider " if confidence > 0.6 else "Je ne suis pas sûr d’avoir compris. Peux-tu reformuler ?"
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
                            print(" Envoi du message à WhatsApp...")
                            send_message_to_whatsapp(from_number, response, vendeur)
                            print(" Message WhatsApp envoyé avec succès.")
                        except Exception as send_err:
                            print(" Erreur lors de l'envoi :", send_err)
                    else:
                        print(" Aucun vendeur trouvé pour ce phone_number_id :", phone_number_id)

        except Exception as global_err:
            print(" Erreur globale webhook :", global_err)
            return HttpResponse("Erreur interne", status=500)

        return HttpResponse("EVENT_RECEIVED", status=200)

    return HttpResponse("Méthode non autorisée", status=405)

class ProductDetailAPIView(RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsVendeur]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsVendeur])
def toggle_global_bot(request):
    status = request.data.get("status")

    if isinstance(status, str):
        status = status.lower() == "true"

    if not isinstance(status, bool):
        return Response({"error": "Le champ 'status' doit être un booléen."}, status=400)

    request.user.bot_enabled = status
    request.user.save()

    return Response({
        "status": "activé" if status else "désactivé",
        "message": "Bot mis à jour avec succès."
    })

@api_view(['GET'])
def get_product_details(request, id):
    if not request.user.is_authenticated or not request.user.is_vendeur:
        return Response({"detail": "Non autorisé."}, status=403)

    try:
        product = Product.objects.get(id=id, user=request.user)
    except Product.DoesNotExist:
        return Response({"detail": "Produit introuvable."}, status=404)

    serializer = ProductDetailSerializer(product, context={"request": request})
    return Response(serializer.data)