import spacy
from sklearn.metrics import classification_report

nlp = spacy.load("bot_nlp_model/model-best")

# Ensemble de test élargi (15 exemples)
test_samples = [
    ("bonjour", "salutation"),
    ("salut l'équipe", "salutation"),
    ("je veux acheter", "commande"),
    ("passer commande", "commande"),
    ("vos horaires ?", "horaire"),
    ("vous ouvrez quand ?", "horaire"),
    ("moyens de paiement", "paiement"),
    ("payer par mobile money", "paiement"),
    ("quel temps à Abidjan ?", "rejet"),
    ("tu connais la dernière chanson ?", "rejet"),
    ("blabla incompréhensible", "rejet"),
    ("bonjour je veux payer", "paiement"),  # Test mixte
    ("salut c'est quoi vos horaires", "horaire"),  # Test mixte
    ("je déteste ce produit", "retour"),  # Test nouvelle intention
    ("livraison gratuite ?", "livraison")  # Test nouvelle intention
]

def evaluate_model():
    y_true, y_pred = [], []
    for text, true_label in test_samples:
        doc = nlp(text.lower())
        pred_label = max(doc.cats.items(), key=lambda x: x[1])[0] if doc.cats else "rejet"
        y_true.append(true_label)
        y_pred.append(pred_label)
        print(f"Text: {text[:30]:<30} | True: {true_label:<10} | Pred: {pred_label:<10} | Conf: {max(doc.cats.values()):.2f}")
    
    print("\nRapport Détaillé :")
    print(classification_report(y_true, y_pred))

if __name__ == "__main__":
    evaluate_model()