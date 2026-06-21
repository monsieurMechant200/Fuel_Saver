"""Paramètres globaux, thème visuel et contenus narratifs de FuelSaver.

Ce module centralise toutes les constantes du jeu : densités de génération
des niveaux, palette de couleurs, skins disponibles et textes d'introduction
des chapitres. Aucune valeur n'a été modifiée par rapport à la version
originale du script.
"""

import os
import sys


def get_data_path() -> str:
    """Détermine le dossier de stockage des données utilisateur (scores).

    - Application compilée (PyInstaller, ...) : dossier standard de l'OS.
    - Mode développement : dossier du paquet.
    """
    if getattr(sys, "frozen", False):
        if sys.platform == "win32":
            base = os.environ.get("APPDATA", os.path.expanduser("~"))
            return os.path.join(base, "FuelSaver")
        if sys.platform == "darwin":
            return os.path.join(
                os.path.expanduser("~"), "Library", "Application Support", "FuelSaver"
            )
        return os.path.join(os.path.expanduser("~"), ".local", "share", "FuelSaver")
    return os.path.dirname(os.path.abspath(__file__))


# ----------------------------------------------------------------------
# Stockage des données utilisateur (scores)
# ----------------------------------------------------------------------
DATA_PATH = get_data_path()
os.makedirs(DATA_PATH, exist_ok=True)
SCORES_FILE = os.path.join(DATA_PATH, "fuelsaver_scores.json")

# ----------------------------------------------------------------------
# Constantes de jeu
# ----------------------------------------------------------------------
ENERGIE_MAX = 20
PICKUP_PROB = 0.12
ENEMY_PROB = 0.08
PORTAL_PROB = 0.03
PORTAL_PAIRS = 3

# ----------------------------------------------------------------------
# Thème visuel
# ----------------------------------------------------------------------
NEON = {
    0: "#F4E3B2",   # or clair (low cost)
    1: "#A8E6CF",   # menthe douce
    2: "#9BB7D4",   # bleu pastel
    3: "#FAC0D9",   # rose poudré
    9: "#2D3A4A",   # obstacle sombre mais pas noir
    "enemy": "#FF8A8A",
    "treasure": "#FFE55C",
    "portal": "#C5A3FF",
}

SKINS = {
    "👾": {"color": "#FF8A9F"},
    "🧑‍🚀": {"color": "#A0D6B4"},
    "🐱": {"color": "#F9D77E"},
    "🤖": {"color": "#A997DF"},
}

# ----------------------------------------------------------------------
# Textes contextuels pour chaque niveau (3 par niveau)
# ----------------------------------------------------------------------
LEVEL_STORIES = {
    "La Rue": [
        "Don Juan quitte sa demeure, le cœur léger. La rue est sombre, des ennemis "
        "rôdent, mais il sait que Lilith l'attend. Il doit traverser ce quartier "
        "malfamé sans attirer l'attention.",
        "Les pavés glissants et les ruelles étroites compliquent sa progression. "
        "Des ombres suspectes se cachent derrière chaque angle. Don Juan avance "
        "prudemment, économisant ses forces.",
        "Une rumeur court : Pedro a posté des gardes aux carrefours. Don Juan doit "
        "choisir ses pas avec soin pour éviter les patrouilles et rejoindre le jardin.",
    ],
    "Le Jardin": [
        "Le jardin est luxuriant, mais dangereux. Des buissons épineux et des "
        "statues animées bloquent le passage. Don Juan se faufile entre les roses, "
        "guidé par le parfum de Lilith.",
        "Une fontaine magique brille au loin ; on dit qu'elle redonne de l'énergie. "
        "Mais des gardes rôdent, prêts à donner l'alerte. Chaque pas doit être calculé.",
        "Le labyrinthe de haies désoriente Don Juan. Il doit trouver la sortie avant "
        "que la nuit ne tombe, car les créatures nocturnes deviennent plus agressives.",
    ],
    "La Maison": [
        "Enfin la maison de Pedro se dresse devant lui. Mais les fenêtres sont "
        "gardées et la porte d'entrée est verrouillée. Don Juan cherche une entrée "
        "discrète.",
        "Des pièges mécaniques protègent les abords. Un faux mouvement et c'est la "
        "fin. Don Juan se concentre, son cœur bat pour Lilith.",
        "Les murmures des domestiques lui indiquent que Pedro est absent pour "
        "l'instant. C'est le moment ou jamais de pénétrer dans la place.",
    ],
    "La Chambre": [
        "Dernière étape : la chambre de Lilith. Le couloir est long et semé "
        "d'embûches. Don Juan sent sa présence de l'autre côté de la porte.",
        "Des portraits aux yeux mobiles le surveillent. Il doit se déplacer sans "
        "faire de bruit, en retenant son souffle.",
        "Plus que quelques pas. L'énergie lui manque, mais l'amour le porte. Il "
        "rassemble ses dernières forces pour atteindre sa bien-aimée.",
    ],
}
