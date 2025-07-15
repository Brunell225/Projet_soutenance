import json
import spacy
from pathlib import Path
from random import choice
import openai

from .config.nlp_settings import NLP_CONFIG

# === Chargement des chemins
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "bot" / "bot_nlp_model" / "model-best"
INTENTIONS_PATH = BASE_DIR / "bot" / "intentions.json"
TRAIN_INTENTS_PATH = BASE_DIR / "bot" / "train_intents.json"

# === Chargement modèle spaCy
try:
    nlp = spacy.load(str(MODEL_PATH))
except Exception as e:
    print(f"❌ Erreur chargement modèle spaCy : {e}")
    nlp = None

# === Chargement des intentions combinées
def load_combined_intents():
    def load_json(path):
        try:
            with open(BASE_DIR / "bot" / path, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Fichier manquant : {path}")
            return {}
        except json.JSONDecodeError:
            print(f"⚠️ JSON invalide dans : {path}")
            return {}

    base = load_json("intentions.json")
    extra = load_json("train_intents.json")

    for intent, phrases in extra.items():
        base[intent] = list(set(base.get(intent, []) + phrases))
    return base

INTENT_KEYWORDS = load_combined_intents()
STYLE_VARIANTS = NLP_CONFIG.get("STYLE_VARIANTS", {})
FALLBACKS = NLP_CONFIG.get("FALLBACK_RESPONSES", ["Je suis là pour t'aider 😉"])
TRIGGERS = NLP_CONFIG.get("KEYWORD_TRIGGERS", {})
INTENT_PRIORITY = {"règles": 3, "nlp": 2, "openai": 1}

# === 1. Règles simples (triggers manuels)
def rule_based_detect(text):
    text = text.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return intent
    for intent, config in TRIGGERS.items():
        for kw in config.get("keywords", []):
            if kw in text:
                return intent
    return None

# === 2. Détection NLP (spaCy)
def spaCy_detect(text):
    if not nlp:
        return None, 0.0
    doc = nlp(text.lower())
    if doc.cats:
        intent, score = max(doc.cats.items(), key=lambda x: x[1])
        if score >= NLP_CONFIG["MIN_CONFIDENCE"]:
            return intent, score
    return None, 0.0

# === 3. Détection via OpenAI (fallback)
def openai_detect(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un assistant d'une boutique ivoirienne. Donne uniquement l'intention du message (un seul mot)."
                },
                {"role": "user", "content": f"Quel est l’intention du message : '{text}' ?"}
            ],
            temperature=0.3
        )
        intent = response.choices[0].message.content.strip().lower().split()[0].strip(",.!?")
        return intent, 0.7
    except openai.OpenAIError:
        return "inconnu", 0.0

# === 4. Pipeline complet
def detect_intent_pipeline(text):
    candidates = []

    # a. Règles
    rule = rule_based_detect(text)
    if rule:
        candidates.append({"intent": rule, "score": 1.0, "source": "règles"})

    # b. spaCy
    intent, score = spaCy_detect(text)
    if intent:
        candidates.append({"intent": intent, "score": score, "source": "nlp"})

    # c. OpenAI fallback
    if not candidates or all(c["score"] < 0.5 for c in candidates):
        intent, score = openai_detect(text)
        candidates.append({"intent": intent, "score": score, "source": "openai"})

    # d. Sélection meilleure intention (pondération)
    best = max(candidates, key=lambda c: (c["score"], INTENT_PRIORITY.get(c["source"], 0)))

    # e. Escalade ?
    escalate = False
    if best["intent"] in TRIGGERS:
        escalate = TRIGGERS[best["intent"]].get("escalate", False)

    # f. Logging si inconnu
    if NLP_CONFIG.get("ANALYTICS", {}).get("LOG_MISSED_INTENTS", False):
        if best["intent"] in ["inconnu", "aucune", ""]:
            log_dir = BASE_DIR / "logs"
            log_dir.mkdir(exist_ok=True)
            with open(log_dir / "missed_intents.txt", "a", encoding="utf-8") as f:
                f.write(f"{text.strip()}\n")

    return {
        "intent": best["intent"],
        "score": best["score"],
        "source": best["source"],
        "escalate": escalate
    }

# === 5. Génération de réponse stylisée
def generate_reply(intent):
    if intent in TRIGGERS and isinstance(TRIGGERS[intent], dict):
        return TRIGGERS[intent].get("response")
    if intent in STYLE_VARIANTS:
        return choice(STYLE_VARIANTS[intent])
    return choice(FALLBACKS)
