# Paramètres avancés du NLP

NLP_CONFIG = {
    "MIN_CONFIDENCE": 0.4,

    "FALLBACK_RESPONSES": [
        "Je n'ai pas compris. Pouvez-vous reformuler ?",
        "Pouvez-vous préciser votre demande ?",
        "Je suis désolé, je n'ai pas saisi votre message.",
        "Hmm... un petit effort chef 😅",
        "Essaie encore avec d'autres mots stp 🙏"
    ],

    "KEYWORD_TRIGGERS": {
        "urgence": ["urgent", "important", "vite", "urgence", "très urgent", "immédiatement", "besoin rapide", "c’est pressé"],
        "humain": ["parler à quelqu'un", "conseiller", "agent", "humain", "je veux parler à quelqu’un", "je veux un vrai humain"]
    },

    "STYLE_VARIANTS": {
        "salutation": [
            "Bjr le boss 👋 ! Je suis là pour vous.",
            "Bienvenue ooo 🙏, dites-moi tout 👂",
            "Salut 👋, vous êtes à la bonne adresse 😎",
            "Bons retours 🙌 ! Que puis-je faire pour vous ?",
            "Yoo , tu as besoin de quoi 🔥",
            "Akouaba 🙏🏾, que puis-je faire pour toi ?"
        ],
        "remerciement": [
            "Merci hein 🙏, ça fait plaisir 💙",
            "C’est vous les vrais 👊🏾",
            "Merci beaucoup ooo ! On est ensemble 💪🏾",
            "Toujours là pour vous, le client est roi 👑",
            "Big merci boss 👏🏾",
            "On avance grâce à vous 🙌"
        ],
        "commande": [
            "C’est noté chef 📝. Envoyez les détails.",
            "Bon choix 😍. Donnez la taille, couleur et quantité.",
            "On emballe ça direct 🛍️🔥",
            "Go pour la commande ✅. On attend vos infos.",
            "On prépare ça rapido pour vous 💨",
            "Envoyez juste vos préférences, on gère 🙌"
        ],
        "produit": [
            "Voici ce qu’on a en stock 👇🏾",
            "Les meilleurs articles du moment sont là 🛒",
            "J’ai mis les bons trucs pour toi ici 👌🏾",
            "Regarde un peu ça 😎👇🏾",
            "Tu vas aimer ce qu’on propose 😍",
            "On a de tout, regarde un peu 👀"
        ],
        "livraison": [
            "Livraison dispo sur Abidjan et intérieur du pays 🚚🇨🇮",
            "On livre rapido 💨, où que vous soyez 💪🏾",
            "Voici comment ça se passe pour la livraison 📦",
            "Zéro stress, on vous dépose ça chez vous 🏠",
            "Les frais dépendent de la zone, on vous explique 💬",
            "Livraison assurée avec soin 👌🏾"
        ],
        "paiement": [
            "Orange Money, Moov Money, MTN, tout est bon 💰📱",
            "Vous pouvez payer en toute sécurité 🔒",
            "Pas besoin de vous déplacer, tout se fait en ligne 📲",
            "Vous voulez payer comment ? On s’adapte 💳",
            "Paiement simple et rapide, comme on aime 😎",
            "On accepte tout mode moderne 💵"
        ],
        "retour": [
            "Y a pas match ? Pas de souci, on peut changer ça 🔄",
            "Le retour est possible dans les 7 jours 👌🏾",
            "Je vous explique comment retourner l’article 💬",
            "On va arranger ça ensemble 🙏",
            "On s’en occupe, ne vous inquiétez pas 👌🏾",
            "Retour gratuit si besoin chef 😉"
        ],
        "problème": [
            "Aïe 😟. On va corriger ça vite fait bien fait.",
            "On s’en occupe tout de suite, pardon 🙏🏾",
            "Merci de votre patience 🙏. On va gérer ça.",
            "Petit souci ? On va débrouiller ça 😎",
            "Dites-moi tout, on va arranger 💡",
            "Oups 😬, je gère ça pour vous maintenant"
        ],
        "horaire": [
            "On est là tous les jours de 8h à 20h 🕗",
            "Vous pouvez commander à tout moment, on répond vite 💬",
            "Dispo du lundi au samedi 💪🏾",
            "On est connectés ! Écrivez quand vous voulez 👌🏾",
            "Même les dimanches on est là pour vous 🙌🏾",
            "On dort pas chef, on est en ligne 😅"
        ],
        "humain": [
            "Je vous mets en contact avec un conseiller 💬",
            "Quelqu’un va vous répondre très bientôt 🧑🏾‍💻",
            "Je vous laisse avec un humain 🙋🏾‍♂️",
            "Pas de souci. Un agent va reprendre la main 👌🏾",
            "L’équipe va s’occuper de vous, force à vous 💪🏾",
            "Vous passez au service VIP 🛎️"
        ],
        "faq": [
            "Voici les infos qu’il vous faut 👇🏾",
            "J’ai ce qu’il faut pour vous expliquer ça 😎",
            "Regardez ça, ça va vous aider 👇🏾📄",
            "Voici la réponse à votre préoccupation 💬",
            "Je vous éclaire là-dessus 🔦",
            "Petite explication rapide 👉🏾"
        ],
        "rejet": [
            "Pas de souci, je reste dispo si vous changez d’avis 👍🏾",
            "Ok chef, je vous laisse tranquille 👋🏾",
            "Je comprends, à plus tard 🙏🏾",
            "Revenez quand vous voulez 💬",
            "Je suis toujours là au besoin 😇"
        ],
        "annulation": [
            "Ok, on annule ça pour vous 🛑",
            "Commande annulée comme demandé ✂️",
            "C’est noté. Vous pouvez recommencer quand vous voulez 😉",
            "Annulation prise en compte ✅",
            "Pas de souci, c’est fait 👌🏾"
        ],
        "urgent": [
            "Je m’en occupe tout de suite chef ⚡",
            "C’est noté comme prioritaire 🚨",
            "On accélère ça direct 💨",
            "Pas de panique, ça arrive vite 💪🏾",
            "On passe en mode urgence maintenant 🛠️"
        ],
        "avis": [
            "Merci pour votre avis 🙏🏾, ça compte beaucoup !",
            "On prend note de votre retour 💬",
            "Continuez de nous dire ce que vous pensez 💙",
            "On améliore grâce à vous, big up 👊🏾",
            "Merci pour ce retour 🔥",
            "Toujours preneur de feedback 👍🏾"
        ]
    },

    "ANALYTICS": {
    "LOG_MISSED_INTENTS": True,
    "TRACK_CONVERSATION_FLOW": True
}

}
