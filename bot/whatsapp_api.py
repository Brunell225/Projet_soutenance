import requests

def send_message_to_whatsapp(to_number, message, user):
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

    response = requests.post(url, headers=headers, json=data)
    print("✅ Réponse envoyée à WhatsApp:", response.status_code, response.text)
