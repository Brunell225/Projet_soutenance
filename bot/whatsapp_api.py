import requests
import logging

logger = logging.getLogger(__name__)

def send_message_to_whatsapp(to_number, message, user):
    """
    Envoie un message texte WhatsApp à un client via l’API Meta Cloud.
    """
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
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        logger.info(f"✅ Message WhatsApp envoyé à {to_number} - Statut {response.status_code}")
        return response.json()
    except requests.RequestException as e:
        logger.error(f"❌ Erreur lors de l’envoi à {to_number} : {str(e)}")
        return {"error": str(e)}
