import os
import sys
import django

# ➕ Ajoute le chemin du dossier racine du projet (là où se trouve manage.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# 🔧 Déclare le module de configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# 🚀 Initialise Django
django.setup()

# 🤖 Import des modules du bot
from bot.intent_router import detect_intent_pipeline, generate_reply
from bot.escalation import handle_escalation

print("🤖 Bot prêt ! Tape 'exit' pour quitter.\n")

while True:
    user_input = input("🧑 Vous : ").strip()
    if user_input.lower() in ["exit", "quit"]:
        print("👋 Fin de la discussion. À bientôt !")
        break

    result = detect_intent_pipeline(user_input)
    reply = generate_reply(result["intent"])
    print(f"🤖 Bot : {reply}  (Intent: {result['intent']} | Source: {result['source']})")

    if result["escalate"]:
        print("🚨 Escalade détectée ! Un conseiller sera notifié.")
        handle_escalation(user_input, user="TestUser", intent=result["intent"])
