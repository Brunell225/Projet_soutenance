import json
from pathlib import Path
import spacy
from spacy.tokens import DocBin

# Charger le modèle français
nlp = spacy.blank("fr")
db = DocBin()

with open("training_data/train_intents.json", "r", encoding="utf-8") as f:
    training_data = json.load(f)

for item in training_data:
    doc = nlp.make_doc(item["text"])
    doc.cats = {item["intent"]: 1.0}
    db.add(doc)

output_path = Path("training_data/train.spacy")
db.to_disk(output_path)
print("✅ Données converties dans training_data/train.spacy")
