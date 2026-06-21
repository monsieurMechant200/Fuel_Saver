"""Gestion de la persistance des meilleurs scores (high scores)."""

import json
import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)


class ScoreManager:
    """Charge, met à jour et sauvegarde les meilleurs scores sur disque (JSON)."""

    def __init__(self, scores_file: str) -> None:
        self.scores_file = scores_file
        self.high_scores: Dict[str, int] = self._load()

    def _load(self) -> Dict[str, int]:
        if not os.path.exists(self.scores_file):
            return {}
        try:
            with open(self.scores_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Impossible de charger les scores (%s) : %s", self.scores_file, exc)
            return {}

    def save(self) -> None:
        try:
            with open(self.scores_file, "w", encoding="utf-8") as f:
                json.dump(self.high_scores, f)
        except OSError as exc:
            logger.error("Impossible d'enregistrer les scores (%s) : %s", self.scores_file, exc)

    def get(self, level_name: str, solo: bool) -> int:
        """Renvoie le meilleur score connu pour un chapitre, en mode solo ou versus."""
        key = f"{level_name}_solo" if solo else f"{level_name}_versus"
        return self.high_scores.get(key, 0)

    def update(self, level_name: str, energy_left: float, solo: bool) -> None:
        """Met à jour (et sauvegarde) le meilleur score si la performance est améliorée."""
        key = f"{level_name}_solo" if solo else f"{level_name}_versus"
        energy_left = int(energy_left)
        if key not in self.high_scores or energy_left > self.high_scores[key]:
            self.high_scores[key] = energy_left
            self.save()
