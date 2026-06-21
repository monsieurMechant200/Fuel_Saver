"""Modèle représentant un joueur (Don Juan ou Pedro)."""

from typing import List, Tuple

from fuelsaver.config import ENERGIE_MAX

Position = Tuple[int, int]


class Player:
    """État d'un joueur : position, énergie, skin et éléments graphiques associés."""

    def __init__(self, name: str, skin: str, start_pos: Position, color: str) -> None:
        self.name = name
        self.skin = skin
        self.pos = start_pos
        self.energy = ENERGIE_MAX
        self.color = color
        self.alive = True
        self.won = False
        self.canvas_ids: List[int] = []
