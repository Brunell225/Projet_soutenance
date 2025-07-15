# bot/handlers.py
from .intent_router import detect_intent_pipeline, generate_reply
from .escalation import handle_escalation

def handle_user_message(user, message_text):
    intent_data = detect_intent_pipeline(message_text)
    intent = intent_data["intent"]
    reply = generate_reply(intent)

    if intent_data.get("escalate", False):
        handle_escalation(message_text, user=user, intent=intent)

    return reply
