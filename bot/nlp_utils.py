import os
import json
import re
import spacy
from typing import Tuple, Optional, List
from pathlib import Path
from dotenv import load_dotenv
from django.db.models import Q
from .intent_router import detect_intent_pipeline

load_dotenv()

# === Chemins projet ===
PROJECT_ROOT = Path(__file__).parent
MODEL_DIR = PROJECT_ROOT / "bot_nlp_model" / "model-best"
INTENTIONS_FILE = PROJECT_ROOT / "intentions.json"
TRAIN_INTENTS_FILE = PROJECT_ROOT / "train_intents.json"

# === Chargement modèle spaCy
nlp_intent = None
try:
    if MODEL_DIR.exists():
        nlp_intent = spacy.load(MODEL_DIR)
        print(" Modèle NLP chargé avec succès")
    else:
        print(f" Modèle NLP introuvable à l'emplacement: {MODEL_DIR}")
except Exception as e:
    print(f" Erreur chargement modèle NLP : {e}")
    nlp_intent = None

# === 1. Détection intention
def detect_intention(message: str) -> Tuple[Optional[str], float, Optional[str]]:
    if not message:
        return None, 0.0, None
    try:
        result = detect_intent_pipeline(message)
        if isinstance(result, dict):
            return result.get("intent"), result.get("score", 1.0), result.get("source")
        elif isinstance(result, str):
            return result, 1.0, "règles"
        return None, 0.0, None
    except Exception as e:
        print(f" Erreur dans detect_intention (pipeline) : {e}")
        return None, 0.0, None

# === 2. Extraction de mots-clés
def extract_keywords(text: str) -> List[str]:
    if not text:
        return []

    text = text.lower()
    keywords = set()

    keyword_config = {
        "colors": ["noir", "blanc", "bleu", "rouge", "vert", "jaune", "gris", "rose", "marron", "orange"],
        "shoe_sizes": [str(i) for i in range(35, 48)],
        "sizes": ["xs", "s", "m", "l", "xl", "xxl", "xxxl", "taille unique"],
        "products": [
            "chaussure", "tenue", "robe", "chemise", "pantalon", "jean", "short", "sac", 
            "bijou", "montre", "casquette", "t-shirt", "baskets", "claquette", "costume",
            "vêtement", "ensemble", "sandale", "collier", "lunette", "sneakers"
        ]
    }

    for terms in keyword_config.values():
        for term in terms:
            pattern = rf"\b{term}s?\b"
            if re.search(pattern, text):
                keywords.add(term)

    return sorted(keywords)

# === 3. Génération de tags
def generate_tags(text: str) -> List[str]:
    return [kw for kw in extract_keywords(text) if len(kw) > 2]

# === 4. Recherche intelligente de produits
def search_products(user, message_text: str) -> List:
    """
    Recherche des produits correspondants à partir du message du client.
    """
    from .models import Product  # Import local pour éviter les boucles

    if not message_text or not user:
        return []

    keywords = extract_keywords(message_text)
    if not keywords:
        return []

    query = Q()
    for kw in keywords:
        query |= Q(name__icontains=kw)
        query |= Q(tags__icontains=kw)
        query |= Q(colors__icontains=kw)
        query |= Q(sizes__icontains=kw)

    return Product.objects.filter(user=user, is_available=True).filter(query).distinct()[:5]

# === 5. Vérification des intentions manquantes
def validate_intent_coverage():
    try:
        train_intents = set()
        if TRAIN_INTENTS_FILE.exists():
            with open(TRAIN_INTENTS_FILE, 'r', encoding='utf-8') as f:
                train_intents = set(json.load(f).keys())

        keyword_intents = set()
        if INTENTIONS_FILE.exists():
            with open(INTENTIONS_FILE, 'r', encoding='utf-8') as f:
                keyword_intents = set(json.load(f).keys())

        missing = train_intents - keyword_intents
        if missing:
            print(f" Intentions manquantes dans intentions.json : {missing}")

        overlap = train_intents & keyword_intents
        if not overlap:
            print(" Aucune intention commune détectée. Vérifiez vos fichiers JSON.")
    except Exception as e:
        print(f" Erreur validation intentions : {e}")

# === 6. Test manuel
if __name__ == "__main__":
    print("\n=== Vérification fichiers ===")
    print(f"MODEL_DIR: {MODEL_DIR} - Existe: {MODEL_DIR.exists()}")
    print(f"INTENTIONS_FILE: {INTENTIONS_FILE} - Existe: {INTENTIONS_FILE.exists()}")
    print(f"TRAIN_INTENTS_FILE: {TRAIN_INTENTS_FILE} - Existe: {TRAIN_INTENTS_FILE.exists()}")
    validate_intent_coverage()
    print(" Initialisation terminée")
