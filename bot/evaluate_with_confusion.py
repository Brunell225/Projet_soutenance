import numpy as np
import spacy
import json
import os
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, f1_score

# Configuration sans affichage interactif (utile pour les serveurs)
plt.switch_backend('Agg')

# 📌 Chemin vers le modèle
MODEL_PATH = "bot_nlp_model/model-best"
if not Path(MODEL_PATH).exists():
    raise FileNotFoundError(f"❌ Le modèle spaCy '{MODEL_PATH}' est introuvable.")

# Chargement du modèle spaCy
nlp = spacy.load(MODEL_PATH)

def load_test_data(file_path):
    if not Path(file_path).exists():
        raise FileNotFoundError(f"❌ Fichier de test introuvable : {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def evaluate_model(test_data):
    y_true, y_pred, texts = [], [], []

    for intent, examples in test_data.items():
        for text in examples:
            doc = nlp(text.lower())
            pred = max(doc.cats.items(), key=lambda x: x[1])[0] if doc.cats else "rejet"
            y_true.append(intent)
            y_pred.append(pred)
            texts.append(text)

    return y_true, y_pred, texts

def save_results(y_true, y_pred, texts, report, timestamp):
    results = pd.DataFrame({
        "Text": texts,
        "True_Label": y_true,
        "Predicted_Label": y_pred
    })
    results.to_csv(f"evaluation_results_{timestamp}.csv", index=False)
    
    with open(f"classification_report_{timestamp}.txt", "w", encoding="utf-8") as f:
        f.write(report)

def generate_confusion_matrix(y_true, y_pred, labels, timestamp):
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    fig, ax = plt.subplots(figsize=(12, 10))
    
    cax = ax.matshow(cm, cmap='Blues')
    plt.colorbar(cax)

    for (i, j), val in np.ndenumerate(cm):
        ax.text(j, i, f"{val}", ha='center', va='center', 
                color='red' if val > cm.max()/2 else 'black')

    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Prédictions")
    ax.set_ylabel("Vraies étiquettes")
    plt.title("Matrice de Confusion", pad=20)
    
    plt.tight_layout()
    plt.savefig(f"confusion_matrix_{timestamp}.png")
    print(f"✅ Matrice de confusion sauvegardée dans confusion_matrix_{timestamp}.png")

if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    # Chargement des données
    test_data = load_test_data("train_intents.json")

    # Évaluation
    y_true, y_pred, texts = evaluate_model(test_data)
    report = classification_report(y_true, y_pred)

    # Sauvegarde
    save_results(y_true, y_pred, texts, report, timestamp)

    all_labels = sorted(set(y_true + y_pred))
    generate_confusion_matrix(y_true, y_pred, all_labels, timestamp)

    print("\n=== 📄 Rapport de Classification ===")
    print(report)
    print(f"\n📊 Score F1 Macro: {f1_score(y_true, y_pred, average='macro'):.2f}")

    print("\n=== 📂 Fichiers Générés ===")
    print(f"- evaluation_results_{timestamp}.csv")
    print(f"- classification_report_{timestamp}.txt")
    print(f"- confusion_matrix_{timestamp}.png")
