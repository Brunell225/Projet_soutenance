import json

# Charger les intentions depuis train_intents.json
with open("train_intents.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Créer un fichier JSONL compatible spaCy
with open("train_data.jsonl", "w", encoding="utf-8") as out_file:
    for intent, examples in data.items():
        for example in examples:
            json_line = {
                "text": example,
                "cats": {intent: 1.0}
            }
            out_file.write(json.dumps(json_line, ensure_ascii=False) + "\n")

print("✅ Conversion terminée : train_data.jsonl prêt pour spaCy")
