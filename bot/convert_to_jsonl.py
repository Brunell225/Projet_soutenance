import json

with open("train_intents.json", "r", encoding="utf-8") as f:
    data = json.load(f)

with open("train_data.jsonl", "w", encoding="utf-8") as out_file:
    for item in data:
        json_line = {
            "text": item["text"],
            "cats": {item["intent"]: 1.0}
        }
        out_file.write(json.dumps(json_line, ensure_ascii=False) + "\n")
