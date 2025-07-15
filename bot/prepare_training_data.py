import json
import spacy
from pathlib import Path
from spacy.training import Example
from spacy.tokens import DocBin

BASE_DIR = Path(__file__).resolve().parent
nlp = spacy.blank("fr")  # Langue française
output_dir = BASE_DIR / "training_data"
output_dir.mkdir(exist_ok=True)

with open(BASE_DIR / "train_intents.json", encoding="utf-8") as f:
    data = json.load(f)

examples = []

for intent, phrases in data.items():
    for phrase in phrases:
        doc = nlp.make_doc(phrase)
        cats = {label: 0.0 for label in data.keys()}
        cats[intent] = 1.0
        example = Example.from_dict(doc, {"cats": cats})
        examples.append(example)

# Créer et sauvegarder le DocBin
docbin = DocBin(store_user_data=True)
for example in examples:
    docbin.add(example.reference)

docbin.to_disk(output_dir / "train.spacy")
print(" Données .spacy sauvegardées dans :", output_dir / "train.spacy")
