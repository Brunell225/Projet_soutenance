import spacy
from spacy.util import minibatch
from pathlib import Path
import random
import json
import os

# === Paramètres ===
MODEL_OUTPUT_DIR = "bot_nlp_model"
TRAINING_DATA_PATH = os.path.join(os.path.dirname(__file__), "train_intents.json")

# === Charger les données ===
def load_data():
    with open(TRAINING_DATA_PATH, encoding='utf-8') as f:
        data = json.load(f)
    return [(item["text"], item["intent"]) for item in data]

# === Préparer les données pour spaCy ===
def prepare_training_data(data):
    categories = set(intent for _, intent in data)
    training_data = []

    for text, intent in data:
        cats = {cat: (cat == intent) for cat in categories}
        training_data.append((text, {"cats": cats}))

    return training_data

# === Entraîner le modèle ===
def train_model(train_data, n_iter=10):
    nlp = spacy.blank("fr")
    text_cat = nlp.add_pipe("textcat", last=True)

    # Ajouter les labels à partir des données
    labels = set()
    for _, annotations in train_data:
        for label in annotations["cats"]:
            labels.add(label)
    for label in labels:
        text_cat.add_label(label)

    # Préparer les exemples
    training_examples = []
    for text, annotations in train_data:
        doc = nlp.make_doc(text)
        example = spacy.training.Example.from_dict(doc, annotations)
        training_examples.append(example)

    # Entraînement
    optimizer = nlp.begin_training()
    for i in range(n_iter):
        random.shuffle(training_examples)
        losses = {}
        batches = minibatch(training_examples, size=8)

        for batch in batches:
            nlp.update(batch, drop=0.2, losses=losses)

        print(f"Iteration {i+1}: Losses {losses}")

    # Sauvegarde
    output_dir = Path(MODEL_OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)
    nlp.to_disk(output_dir)
    print(f"✅ Modèle entraîné enregistré dans : {output_dir.absolute()}")

# === Lancer l'entraînement ===
if __name__ == "__main__":
    print("📦 Chargement des données...")
    raw_data = load_data()
    train_data = prepare_training_data(raw_data)
    train_model(train_data)
