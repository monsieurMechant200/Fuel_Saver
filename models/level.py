"""Modèle de niveau : génération de la carte, calcul HJB, portails, ennemis et trésors."""

import heapq
import random
from collections import deque
from typing import Dict, Optional, Set, Tuple

import numpy as np

Position = Tuple[int, int]


class Level:
    """Contient la carte, les valeurs HJB et les éléments spéciaux d'un chapitre."""

    def __init__(
        self,
        name: str,
        size: int,
        obstacle_density: float,
        enemy_density: float,
        treasure_density: float,
        portal_count: int,
    ) -> None:
        self.name = name
        self.size = size
        self.obstacle_density = obstacle_density
        self.enemy_density = enemy_density
        self.treasure_density = treasure_density
        self.portal_count = portal_count
        self.grid: Optional[np.ndarray] = None
        self.enemies: Set[Position] = set()
        self.treasures: Set[Position] = set()
        self.portals: Dict[Position, Position] = {}
        self.start: Position = (0, 0)
        self.home: Position = (size - 1, size - 1)
        self.hjb: Optional[np.ndarray] = None
        self.generate()  # garantit un chemin existant

    # ------------------------------------------------------------------
    # Génération de la carte
    # ------------------------------------------------------------------
    def generate(self, max_attempts: int = 100) -> None:
        """Génère une carte avec au moins un chemin de start à home."""
        for _attempt in range(max_attempts):
            self._generate_random()
            if self._has_path():
                self.compute_hjb()
                return
        # Si échec, on force un chemin simple
        self._generate_simple_path()

    def _generate_random(self) -> None:
        s = self.size
        self.grid = np.random.choice([1, 2, 3], size=(s, s))
        for i in range(s):
            for j in range(s):
                if (i, j) == self.start or (i, j) == self.home:
                    continue
                if random.random() < self.obstacle_density:
                    self.grid[i, j] = 9

        self.enemies.clear()
        self.treasures.clear()

        for i in range(s):
            for j in range(s):
                if self.grid[i, j] != 9 and (i, j) not in (self.start, self.home):
                    if random.random() < self.enemy_density:
                        self.enemies.add((i, j))

        for i in range(s):
            for j in range(s):
                if (
                    self.grid[i, j] != 9
                    and (i, j) not in (self.start, self.home)
                    and (i, j) not in self.enemies
                ):
                    if random.random() < self.treasure_density:
                        self.treasures.add((i, j))

        self._place_portals()
        self.enemies.discard(self.start)
        self.enemies.discard(self.home)
        self.treasures.discard(self.start)
        self.treasures.discard(self.home)

    def _generate_simple_path(self) -> None:
        """Crée un chemin simple en cas d'échec de génération aléatoire."""
        s = self.size
        self.grid = np.ones((s, s), dtype=int) * 2  # coût moyen
        # Chemin en ligne droite (par exemple)
        for i in range(s):
            self.grid[i, 0] = 1
            self.grid[0, i] = 1
        self.grid[self.start] = 1
        self.grid[self.home] = 1
        self.enemies.clear()
        self.treasures.clear()
        self.portals.clear()
        self.compute_hjb()

    def _has_path(self) -> bool:
        """Vérifie avec un parcours en largeur s'il existe un chemin de start à home."""
        s = self.size
        visited: Set[Position] = set()
        queue = deque([self.start])
        while queue:
            i, j = queue.popleft()
            if (i, j) == self.home:
                return True
            if (i, j) in visited:
                continue
            visited.add((i, j))
            for ni, nj in [(i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)]:
                if 0 <= ni < s and 0 <= nj < s and self.grid[ni, nj] != 9 and (ni, nj) not in visited:
                    queue.append((ni, nj))
        return False

    def _place_portals(self) -> None:
        free_cells = [
            (i, j)
            for i in range(self.size)
            for j in range(self.size)
            if self.grid[i, j] != 9
            and (i, j) != self.start
            and (i, j) != self.home
            and (i, j) not in self.enemies
            and (i, j) not in self.treasures
        ]
        random.shuffle(free_cells)
        for k in range(0, min(self.portal_count * 2, len(free_cells) - 1), 2):
            if k + 1 < len(free_cells):
                self.portals[free_cells[k]] = free_cells[k + 1]
                self.portals[free_cells[k + 1]] = free_cells[k]

    # ------------------------------------------------------------------
    # Coûts et équation HJB
    # ------------------------------------------------------------------
    def cost_at(self, pos: Position) -> int:
        i, j = pos
        base = self.grid[i, j]
        if base == 9:
            return 9
        cost = base
        if pos in self.enemies:
            cost += 2
        return cost

    def compute_hjb(self) -> None:
        """Calcule les valeurs HJB (coût optimal vers `home`) via Dijkstra."""
        s = self.size
        self.hjb = np.full((s, s), 1e9)
        self.hjb[self.home] = 0
        pq = [(0, self.home)]
        visited: Set[Position] = set()
        while pq:
            dist, (i, j) = heapq.heappop(pq)
            if (i, j) in visited:
                continue
            visited.add((i, j))
            for ni, nj in [(i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)]:
                if 0 <= ni < s and 0 <= nj < s and self.grid[ni, nj] != 9:
                    new_dist = dist + self.cost_at((ni, nj))
                    if new_dist < self.hjb[ni, nj]:
                        self.hjb[ni, nj] = new_dist
                        heapq.heappush(pq, (new_dist, (ni, nj)))
            if (i, j) in self.portals:
                exit_pos = self.portals[(i, j)]
                if self.grid[exit_pos] != 9:
                    if dist < self.hjb[exit_pos]:
                        self.hjb[exit_pos] = dist
                        heapq.heappush(pq, (dist, exit_pos))
