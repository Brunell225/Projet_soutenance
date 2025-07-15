import json
from pathlib import Path
from typing import Dict, Set

def load_json(file_path: str) -> Dict:
    """Charge un fichier JSON avec gestion d'erreur"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def compare_intent_files():
    """Compare les intentions entre les deux fichiers"""
    try:
        # Chargement des données
        intentions = load_json('intentions.json')
        train_intents = load_json('train_intents.json')
        
        # Extraction des clés
        base_intents = set(intentions.keys())
        training_intents = set(train_intents.keys())
        
        # Analyse des différences
        missing_in_train = base_intents - training_intents
        missing_in_base = training_intents - base_intents
        
        # Rapport
        print("🔍 Analyse de Cohérence des Intentions")
        print(f"Total intentions dans intentions.json: {len(base_intents)}")
        print(f"Total intentions dans train_intents.json: {len(training_intents)}")
        
        if missing_in_train:
            print("\n⚠️ Intentions manquantes dans train_intents.json:")
            for intent in sorted(missing_in_train):
                print(f"- {intent} (exemples: {intentions[intent][:3]}...)")
        
        if missing_in_base:
            print("\n⚠️ Intentions manquantes dans intentions.json:")
            for intent in sorted(missing_in_base):
                print(f"- {intent} (exemples: {train_intents[intent][:3]}...)")
        
        if not missing_in_train and not missing_in_base:
            print("\n✅ Les fichiers sont parfaitement synchronisés")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse : {str(e)}")

if __name__ == "__main__":
    compare_intent_files()