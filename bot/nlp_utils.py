import spacy
import os

# === 1. Détection avec le modèle NLP entraîné ===

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(PROJECT_ROOT, "bot_nlp_model")

# Chargement du modèle entraîné
nlp_intent = spacy.load(MODEL_DIR)

def detect_intention_spacy(message):
    doc = nlp_intent(message)
    return doc


# === 2. Extraction de mots-clés produits ===

def extract_keywords(text):
    keywords = []
    text = text.lower()

    colors = ["noir", "noire", "blanc", "bleu", "rouge", "jaune", "vert", "orange", "rose", "gris", "marron"]
    sizes = ["s", "m", "l", "xl", "xxl"]
    shoe_sizes = [str(i) for i in range(30, 50)]

    for color in colors:
        if color in text:
            keywords.append(color)

    for size in sizes:
        if f"taille {size}" in text or f" {size} " in text:
            keywords.append(size)

    for pointure in shoe_sizes:
        if f"pointure {pointure}" in text or f"{pointure}" in text:
            keywords.append(pointure)

    product_types = [
        "chaussure", "chaussures", "sandale", "sandalette", "t-shirt", "tee-shirt", "jean", "bikini",
        "culotte", "maillot", "jupe", "robe", "jogging", "lunette", "bracelet", "chapeau", "talons"
    ]
    for p in product_types:
        if p in text:
            keywords.append(p)

    return list(set(keywords))


# === 3. Alias clair pour le backend ===

def generate_tags(text):
    """
    Génère automatiquement des tags pertinents à partir d’un texte.
    """
    return extract_keywords(text)
