import streamlit as st

st.set_page_config(
    page_title="Stéganographie PNG",
    page_icon="🔒",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.title("Outil de Stéganographie PNG")
st.markdown(
    """
Utilisez la barre latérale pour naviguer :

- **Encoder** — cacher un message secret dans une image PNG
- **Décoder** — extraire un message caché d'une image PNG

---

### Pourquoi PNG uniquement ?

PNG utilise une compression **sans perte** : chaque valeur de pixel est préservée exactement.
Les formats avec perte comme JPEG re-quantifient les pixels lors de la compression et
détruiraient silencieusement les bits cachés.

---

### Méthodes disponibles

| Méthode | Principe | Capacité | Discrétion |
|---|---|---|---|
| **LSB Séquentiel** | Remplace les *n* LSB de chaque pixel sélectionné, dans l'ordre | Très élevée | Faible (détectable statistiquement) |
| **LSB Aléatoire** | Même chose, mais les pixels sont mélangés via un mot de passe | Très élevée | Élevée (indiscernable sans le mot de passe) |
| **Chunk PNG** | Injecte les données dans un chunk ancillaire du fichier | Illimitée | Moyenne (invisible à l'œil, lisible en hex) |
| **Métadonnées tEXt** | Stocke le message dans les métadonnées texte du PNG | Illimitée | Faible (visible dans les propriétés du fichier) |
| **DCT par blocs** | Modifie un coefficient fréquentiel dans chaque bloc 8×8 | Faible | Élevée (résistant aux retouches légères) |

> Pour décoder, utilisez **exactement** la même méthode et les mêmes paramètres qu'à l'encodage.
"""
)
