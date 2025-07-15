import json
import random
import spacy
from spacy.util import minibatch, compounding
from spacy.training.example import Example
from pathlib import Path

def load_training_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # ===== AJOUTEZ ICI LES EXEMPLES NÉGATIFS =====
    negative_examples = [
    ("ça va aujourd'hui ?", {"cats": {"rejet": 1.0}}),
    ("tu es occupé ?", {"cats": {"rejet": 1.0}}),
    ("quel est ton film préféré ?", {"cats": {"rejet": 1.0}}),
    ("comment était ton weekend ?", {"cats": {"rejet": 1.0}}),
    ("tu viens à la fête ce soir ?", {"cats": {"rejet": 1.0}}),
    ("c'est quoi ton signe astro ?", {"cats": {"rejet": 1.0}}),
    ("tu préfères le café ou le thé ?", {"cats": {"rejet": 1.0}}),
    ("quel est le sens de la vie ?", {"cats": {"rejet": 1.0}}),
    ("peux-tu m'aider en maths ?", {"cats": {"rejet": 1.0}}),
    ("quel est ton avis sur la politique ?", {"cats": {"rejet": 1.0}})
]
    # =============================================

    training_data = []
    for intent, examples in data.items():
        for example in examples:
            training_data.append((example, {"cats": {intent: 1.0}}))
    
    training_data.extend(negative_examples)  # On les ajoute au dataset final
    return training_data

def train_spacy_model(train_data, output_dir, n_iter=100):
    # Charger un modèle français de base
    nlp = spacy.blank("fr")
    
    # Configuration du textcat
    config = {
        "threshold": 0.25,
        "model": {
            "@architectures": "spacy.TextCatBOW.v2",
            "exclusive_classes": True,
            "ngram_size": 2,
            "no_output_layer": False
        }
    }
    
    if "textcat" not in nlp.pipe_names:
        textcat = nlp.add_pipe("textcat", config=config)
    else:
        textcat = nlp.get_pipe("textcat")

    # Ajout des labels
    labels = list({label for _, ann in train_data for label in ann["cats"]})
    for label in labels:
        textcat.add_label(label)

    # Paramètres d'entraînement
    optimizer = nlp.begin_training()
    batch_sizes = compounding(4.0, 32.0, 1.5)
    
    print("🚀 Entraînement du modèle NLP (version corrigée)...")
    
    # Créer le dossier principal de sortie d'abord
    main_output_path = Path(output_dir)
    main_output_path.mkdir(parents=True, exist_ok=True)
    
    best_loss = float('inf')
    patience = 3
    
    for i in range(n_iter):
        random.shuffle(train_data)
        losses = {}
        batches = minibatch(train_data, size=batch_sizes)
        
        for batch in batches:
            examples = []
            for text, annotation in batch:
                doc = nlp.make_doc(text)
                example = Example.from_dict(doc, annotation)
                examples.append(example)
            nlp.update(examples, sgd=optimizer, losses=losses, drop=0.3)
        
        current_loss = losses.get("textcat", 1.0)
        print(f"📦 Iteration {i+1} | Loss: {current_loss:.4f}")
        
        # Early stopping
        if current_loss < best_loss:
            best_loss = current_loss
            patience = 3
        else:
            patience -= 1
            if patience <= 0:
                print("✅ Arrêt anticipé (plus d'amélioration)")
                break
        
        # Sauvegarde intermédiaire simplifiée
        if (i+1) % 10 == 0:
            nlp.to_disk(main_output_path / f"iter_{i+1}")

    # Sauvegarde finale
    nlp.to_disk(main_output_path)
    print(f"✅ Modèle final enregistré dans : {main_output_path}")

if __name__ == "__main__":
    train_spacy_model(
        load_training_data("train_intents.json"),
        "bot_nlp_model/model-best"
    )