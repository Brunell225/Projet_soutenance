import os
import sys
import json
import django

# Ajouter le dossier du projet au path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()


from bot.models import BotMessageHistory

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "train_auto.json")

def export_clean_messages(min_confidence=0.8):
    print("🔍 Extraction des messages bien compris...")

    data = []
    qs = BotMessageHistory.objects.filter(
        confidence_score__gte=min_confidence,
        detected_intent__isnull=False
    ).exclude(detected_intent="")

    for h in qs:
        data.append({
            "text": h.client_message,
            "intent": h.detected_intent
        })

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ {len(data)} exemples exportés dans {OUTPUT_PATH}")

if __name__ == "__main__":
    export_clean_messages()
