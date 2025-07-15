import logging
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client

def handle_escalation(message, user=None, intent=None):
    """
    Gère l'escalade : log, envoi d'e-mail et message WhatsApp.
    """
    logging.warning(f"[ESCALADE] Intent critique détecté: {intent} | Message: {message}")

    # 1. Envoi email
    try:
        send_mail(
            subject=f"[BOT ALERT] Escalade - {intent.upper()}",
            message=f"Un utilisateur a envoyé un message critique :\n\n{message}\n\nIntent : {intent}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.SUPPORT_EMAIL],
            fail_silently=True,
        )
    except Exception as e:
        logging.error(f"Erreur envoi mail escalade : {e}")

    # 2. Message WhatsApp (via Twilio)
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            from_='whatsapp:' + settings.TWILIO_WHATSAPP_NUMBER,  # Ex: 'whatsapp:+14155238886'
            to='whatsapp:' + settings.ESCALATION_WHATSAPP_NUMBER,  # Ex: 'whatsapp:+2250102030405'
            body=f"[ALERTE BOT] Intent: {intent}\nMessage: {message}"
        )
    except Exception as e:
        logging.error(f"Erreur envoi WhatsApp escalade : {e}")
