import json
import os

# Chemin d'accès correct
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
input_path = os.path.join(base_dir, "training_data", "train_intents.json")
output_path = os.path.join(base_dir, "training_data", "train.spacy")

from spacy.util import load_config
from spacy.cli.convert import convert

from spacy.tokens import DocBin
import spacy

# Charger le modèle vide
nlp = spacy.blank("fr")
db = DocBin()

with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for item in data:
    doc = nlp.make_doc(item["text"])
    doc.cats = {item["intent"]: 1.0}
    db.add(doc)

db.to_disk(output_path)
print(f"✅ Données converties avec succès → {output_path}")
