# bot/intent_engine.py

from random import choice
from .models import Product
from .config.nlp_settings import NLP_CONFIG

def handle_salutation(message, user):
    return choice([
        "Akwaba ! Que puis-je faire pour toi ?",
        "Bienvenue chez nous  ! Tu veux quoi précisément ?",
        "Salut! Je suis là pour t’aider, parle-moi."
    ])

def handle_commande(message, user):
    return (
        "Tu veux passer une commande ? Super \n"
        "Dis-moi juste :\n"
        "- Le produit\n"
        "- La quantité\n"
        "- Et ton lieu de livraison"
    )

def handle_paiement(message, user):
    return (
        "Voici les moyens de paiement disponibles:\n"
        "- MoMo (Orange, MTN, Moov)\n"
        "- Carte bancaire\n"
        "- Paiement à la livraison"
    )

def handle_remerciement(message, user):
    return choice([
        "Merci à toi aussi  !",
        "Avec plaisir ",
        "Toujours là pour t’aider"
    ])

def handle_rejet(message, user):
    return (
        "Pas de souci . Je suis là si jamais tu changes d’avis."
    )

def handle_unknown(message, user):
    return choice(NLP_CONFIG["FALLBACK_RESPONSES"])


# Le routeur d’intention
def route_intent(intent, message, user):
    handlers = {
        "salutation": handle_salutation,
        "commande": handle_commande,
        "paiement": handle_paiement,
        "remerciement": handle_remerciement,
        "rejet": handle_rejet,
        
    }

    handler = handlers.get(intent, handle_unknown)
    return handler(message, user)
