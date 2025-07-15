import spacy
from spacy.tokens import DocBin
import json

nlp = spacy.blank("fr")  # Langue française
db = DocBin()

with open("train_data.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        example = json.loads(line)
        doc = nlp.make_doc(example["text"])
        doc.cats = example["cats"]
        db.add(doc)

db.to_disk("train.spacy")
