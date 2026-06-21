"""Interface graphique et boucle de jeu principale de FuelSaver.

Cette classe orchestre le menu, l'introduction narrative de chaque chapitre,
le rendu de la carte/des joueurs et la gestion des déplacements (manuels ou
automatiques via les valeurs HJB). La logique de jeu est strictement
identique à la version originale ; seule l'organisation du code a changé.
"""

import logging
import random
import time
import tkinter as tk
from tkinter import Toplevel, messagebox

import customtkinter as ctk

from fuelsaver.config import ENERGIE_MAX, NEON, SKINS, LEVEL_STORIES, SCORES_FILE
from fuelsaver.models import Level, Player
from fuelsaver.services import ScoreManager

logger = logging.getLogger(__name__)

# Apparence globale de CustomTkinter (appliquée avant toute création de fenêtre)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class FuelSaverApp(ctk.CTk):
    """Fenêtre principale et chef d'orchestre du jeu."""

    def __init__(self) -> None:
        super().__init__()
        self.title("FuelSaver – Les Amours de Don Juan")
        self.geometry("1200x800")
        self.minsize(800, 600)
        self.resizable(True, True)

        # États du jeu
        self.levels = self._create_levels()
        self.current_level_idx = 0
        self.level = self.levels[0]
        self.players = []
        self.current_player_idx = 0
        self.game_active = False
        self.animating = False
        self.cell_size = 60  # taille initiale, sera ajustée

        # Infobulle
        self.tooltip_text = None
        self.tooltip_id = None

        # Scores
        self.scores = ScoreManager(SCORES_FILE)

        # Construction du menu
        self._build_menu()

    # ------------------------------------------------------------------
    # Création des niveaux (chapitres)
    # ------------------------------------------------------------------
    def _create_levels(self):
        return [
            Level("La Rue", size=8, obstacle_density=0.05, enemy_density=0.03,
                  treasure_density=0.1, portal_count=1),
            Level("Le Jardin", size=10, obstacle_density=0.10, enemy_density=0.06,
                  treasure_density=0.1, portal_count=2),
            Level("La Maison", size=12, obstacle_density=0.15, enemy_density=0.10,
                  treasure_density=0.1, portal_count=2),
            Level("La Chambre", size=15, obstacle_density=0.20, enemy_density=0.15,
                  treasure_density=0.1, portal_count=3),
        ]

    # ------------------------------------------------------------------
    # Menu principal
    # ------------------------------------------------------------------
    def _build_menu(self) -> None:
        self.menu_frame = ctk.CTkFrame(self, corner_radius=15)
        self.menu_frame.pack(expand=True, fill="both", padx=40, pady=40)

        ctk.CTkLabel(self.menu_frame, text="FUELSAVER", font=("Kanit", 36, "bold"),
                     text_color="#F4E3B2").pack(pady=(20, 10))
        ctk.CTkLabel(self.menu_frame, text="Les Amours de Don Juan", font=("Poppins", 16),
                     text_color="#A8E6CF").pack(pady=(0, 30))

        story = ("Don Juan, le séducteur impénitent, a jeté son dévolu sur Lilith, la femme de Pedro.\n"
                  "Elle l'attend dans leur maison, de l'autre côté de la ville. Mais Pedro veille,\n"
                  "et le chemin est semé d'embûches : ennemis, obstacles et magie noire.\n"
                  "Aidez Don Juan à atteindre Lilith sans tomber à court d'énergie !")
        ctk.CTkLabel(self.menu_frame, text=story, font=("Arial", 12),
                     text_color="#CCCCCC", justify="center", wraplength=700).pack(pady=20)

        # Sélection du niveau
        frame_level = ctk.CTkFrame(self.menu_frame)
        frame_level.pack(pady=10)
        ctk.CTkLabel(frame_level, text="Chapitre :", font=("Arial", 14)).pack(side="left", padx=10)
        self.level_var = ctk.StringVar(value="La Rue")
        level_menu = ctk.CTkOptionMenu(frame_level, values=[l.name for l in self.levels],
                                        variable=self.level_var, width=150)
        level_menu.pack(side="left", padx=10)

        # Mode de jeu
        frame_mode = ctk.CTkFrame(self.menu_frame)
        frame_mode.pack(pady=10)
        self.mode_var = ctk.StringVar(value="Solo")
        ctk.CTkRadioButton(frame_mode, text="Solo (Don Juan)", variable=self.mode_var,
                            value="Solo").pack(side="left", padx=10)
        ctk.CTkRadioButton(frame_mode, text="Versus (Don Juan vs Pedro)", variable=self.mode_var,
                            value="Versus").pack(side="left", padx=10)

        # Choix des skins
        frame_skins = ctk.CTkFrame(self.menu_frame)
        frame_skins.pack(pady=10)
        ctk.CTkLabel(frame_skins, text="Don Juan :", font=("Arial", 12)).grid(row=0, column=0, padx=5)
        self.skin1_var = ctk.StringVar(value="👾")
        skin1_menu = ctk.CTkOptionMenu(frame_skins, values=list(SKINS.keys()),
                                        variable=self.skin1_var, width=80)
        skin1_menu.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(frame_skins, text="Pedro :", font=("Arial", 12)).grid(row=1, column=0, padx=5, pady=(5, 0))
        self.skin2_var = ctk.StringVar(value="🧑‍🚀")
        skin2_menu = ctk.CTkOptionMenu(frame_skins, values=list(SKINS.keys()),
                                        variable=self.skin2_var, width=80)
        skin2_menu.grid(row=1, column=1, padx=5, pady=(5, 0))

        # Bouton "Savoir plus"
        btn_frame = ctk.CTkFrame(self.menu_frame)
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="Savoir plus", font=("Arial", 14),
                      fg_color="#9BB7D4", command=self._show_info).pack(side="left", padx=10)

        # Bouton de démarrage
        ctk.CTkButton(self.menu_frame, text="COMMENCER L'AVENTURE", font=("Arial", 16, "bold"),
                      fg_color="#FAC0D9", hover_color="#D9A5B5", text_color="#1A1A1A",
                      command=self._start_game).pack(pady=20)

        # Meilleurs scores
        self._show_high_scores()

    def _show_high_scores(self) -> None:
        frame = ctk.CTkFrame(self.menu_frame)
        frame.pack(pady=10, fill="x", padx=40)
        ctk.CTkLabel(frame, text="MEILLEURS SCORES", font=("Arial", 14, "bold")).pack()
        text = ""
        for level in self.levels:
            solo = self.scores.get(level.name, solo=True)
            vs = self.scores.get(level.name, solo=False)
            text += f"{level.name}: Solo {solo}  |  Versus {vs}\n"
        ctk.CTkLabel(frame, text=text, font=("Arial", 11), justify="left").pack()

    def _show_info(self) -> None:
        """Ouvre une fenêtre avec l'histoire détaillée et les explications mathématiques."""
        info_win = Toplevel(self)
        info_win.title("Savoir plus")
        info_win.geometry("600x500")
        info_win.configure(bg="#1E2A3A")
        info_win.transient(self)
        info_win.grab_set()

        tabview = ctk.CTkTabview(info_win, width=580, height=450)
        tabview.pack(pady=10, padx=10, expand=True, fill="both")

        # Onglet Histoire
        tab_histoire = tabview.add("Histoire")
        histoire_text = """Don Juan, célèbre séducteur, a rencontré Lilith lors d'un bal masqué. 
Elle est la femme de Pedro, un homme jaloux et puissant. 
Depuis ce jour, Don Juan n'a qu'une obsession : la retrouver. 
Mais Pedro, averti, a protégé sa demeure de nombreux pièges et gardes.

Chaque chapitre représente une étape de cette quête amoureuse :
- La Rue : traverser le quartier hostile.
- Le Jardin : franchir le labyrinthe végétal.
- La Maison : pénétrer dans la demeure de Pedro.
- La Chambre : enfin rejoindre Lilith.

Mais l'énergie de Don Juan est limitée. Il doit optimiser ses déplacements pour arriver à temps.
"""
        ctk.CTkLabel(tab_histoire, text=histoire_text, font=("Arial", 12),
                     text_color="#FFFFFF", wraplength=500, justify="left").pack(pady=20, padx=10)

        # Onglet Mathématiques
        tab_math = tabview.add("Mathématiques")
        math_text = """Le cœur du jeu repose sur l'équation de Hamilton-Jacobi-Bellman (HJB) 
et l'algorithme de Dijkstra.

Principe : Chaque case a un coût (1,2,3) augmenté si un ennemi s'y trouve (+2). 
L'objectif est de minimiser l'énergie dépensée pour atteindre la maison (Lilith).

Équation HJB : V(x) = min_{action} [ coût(x, action) + V(suivant) ]
où V(x) est le coût optimal depuis la case x jusqu'à l'arrivée.

Algorithme de Dijkstra : Il calcule ces valeurs en partant de l'arrivée et en 
propageant les coûts vers l'extérieur. Les portails (coût 0) créent des raccourcis.

Énergie vitale : Le joueur dispose de 20 points d'énergie. Chaque mouvement 
consomme le coût de la case d'arrivée. Les trésors rendent +3. 
Pour gagner, il faut que l'énergie restante soit ≥ 0 à l'arrivée.

🔍 **Stratégie** : Suivre les valeurs HJB affichées sur les cases (petits chiffres) 
permet de choisir le chemin optimal.
"""
        ctk.CTkLabel(tab_math, text=math_text, font=("Arial", 12),
                     text_color="#FFFFFF", wraplength=500, justify="left").pack(pady=20, padx=10)

        ctk.CTkButton(info_win, text="Fermer", command=info_win.destroy,
                      fg_color="#FF8A8A").pack(pady=10)

    # ------------------------------------------------------------------
    # Démarrage du jeu avec synopsis
    # ------------------------------------------------------------------
    def _start_game(self) -> None:
        level_name = self.level_var.get()
        self.current_level_idx = [l.name for l in self.levels].index(level_name)
        self.level = self.levels[self.current_level_idx]

        # Afficher un synopsis aléatoire avant de commencer
        self._show_story_intro(level_name)

    def _show_story_intro(self, level_name: str) -> None:
        """Affiche un texte contextuel pendant 30 secondes avant le début du niveau."""
        stories = LEVEL_STORIES.get(level_name, ["Début de l'aventure..."])
        chosen_story = random.choice(stories)

        intro_win = Toplevel(self)
        intro_win.title(level_name)
        intro_win.geometry("600x300")
        intro_win.configure(bg="#1E2A3A")
        intro_win.transient(self)
        intro_win.grab_set()

        ctk.CTkLabel(intro_win, text=f"Chapitre : {level_name}", font=("Kanit", 20, "bold"),
                     text_color="#F4E3B2").pack(pady=20)

        text_label = ctk.CTkLabel(intro_win, text=chosen_story, font=("Arial", 14),
                                   text_color="#FFFFFF", wraplength=550, justify="center")
        text_label.pack(pady=20, expand=True)

        # Compte à rebours
        time_left = 30
        time_var = tk.StringVar(value=f"Lecture automatique dans {time_left} secondes")
        time_label = ctk.CTkLabel(intro_win, textvariable=time_var, font=("Arial", 10))
        time_label.pack(pady=5)

        def countdown(remaining: int) -> None:
            if remaining <= 0:
                intro_win.destroy()
                self._really_start_game()
            else:
                time_var.set(f"Lecture automatique dans {remaining} secondes")
                intro_win.after(1000, countdown, remaining - 1)

        countdown(time_left)

        ctk.CTkButton(intro_win, text="Commencer maintenant",
                      command=lambda: [intro_win.destroy(), self._really_start_game()],
                      fg_color="#A8E6CF", text_color="#1A1A1A").pack(pady=10)

    def _really_start_game(self) -> None:
        """Lance vraiment la partie après le synopsis."""
        self.players = []
        skin1 = self.skin1_var.get()
        color1 = SKINS[skin1]["color"]
        p1 = Player("Don Juan", skin1, self.level.start, color1)
        self.players.append(p1)

        if self.mode_var.get() == "Versus":
            skin2 = self.skin2_var.get()
            color2 = SKINS[skin2]["color"]
            p2 = Player("Pedro", skin2, self.level.start, color2)
            self.players.append(p2)

        self.current_player_idx = 0
        self.game_active = True

        self.menu_frame.destroy()
        self._build_game_ui()

    # ------------------------------------------------------------------
    # Interface de jeu
    # ------------------------------------------------------------------
    def _build_game_ui(self) -> None:
        self.game_frame = ctk.CTkFrame(self)
        self.game_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # Panneau d'information (gauche)
        self.info_frame = ctk.CTkFrame(self.game_frame, width=300, corner_radius=12)
        self.info_frame.pack(side="left", fill="y", padx=(0, 10))
        self.info_frame.pack_propagate(False)

        ctk.CTkLabel(self.info_frame, text=self.level.name.upper(), font=("Kanit", 18, "bold"),
                     text_color="#F4E3B2").pack(pady=(15, 5))

        self.turn_label = ctk.CTkLabel(self.info_frame, text="", font=("Arial", 14))
        self.turn_label.pack(pady=5)

        self.energy_bars = []
        for p in self.players:
            frame = ctk.CTkFrame(self.info_frame)
            frame.pack(pady=8, padx=10, fill="x")
            ctk.CTkLabel(frame, text=f"{p.name} ({p.skin})", font=("Arial", 12)).pack(anchor="w")
            bar = ctk.CTkProgressBar(frame, width=250, height=15)
            bar.pack(pady=(2, 0))
            bar.set(p.energy / ENERGIE_MAX)
            self.energy_bars.append(bar)

        self.hjb_label = ctk.CTkLabel(self.info_frame, text="HJB à ta position : --", font=("Arial", 11))
        self.hjb_label.pack(pady=10)

        ctk.CTkButton(self.info_frame, text="DÉPLACEMENT AUTO (HJB)", command=self.auto_move,
                      fg_color="#9BB7D4").pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(self.info_frame, text="ABANDONNER", command=self.surrender,
                      fg_color="#FF8A8A").pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(self.info_frame, text="RETOUR AU MENU", command=self.back_to_menu,
                      fg_color="#AAAAAA").pack(pady=20, padx=10, fill="x")

        # Zone de la carte (droite)
        self.canvas_frame = ctk.CTkFrame(self.game_frame, corner_radius=12)
        self.canvas_frame.pack(side="right", expand=True, fill="both")
        self.canvas = tk.Canvas(self.canvas_frame, bg="#1E2A3A", highlightthickness=0)
        self.canvas.pack(expand=True, fill="both")

        # Bindings
        self.canvas.bind("<Motion>", self.on_hover)
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.bind("<KeyPress>", self.on_key_press)
        self.focus_set()

        # Dessin initial
        self._draw_map()
        for p in self.players:
            self._draw_player(p)
        self._update_ui()

    def on_canvas_resize(self, event) -> None:
        """Ajuste la taille des cellules lors du redimensionnement."""
        self.cell_size = min(event.width // self.level.size, event.height // self.level.size)
        self._draw_map()
        for p in self.players:
            self._draw_player(p)

    def _draw_map(self) -> None:
        self.canvas.delete("all")
        s = self.level.size
        cs = self.cell_size
        for i in range(s):
            for j in range(s):
                x1 = j * cs
                y1 = i * cs
                x2 = x1 + cs
                y2 = y1 + cs
                base = self.level.grid[i, j]
                fill = NEON[9] if base == 9 else NEON[base]

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="#2D3A4A", width=1,
                                              tags=("cell", f"cell_{i}_{j}"))

                if (i, j) in self.level.enemies:
                    self.canvas.create_text(x1 + cs // 2, y1 + cs // 2, text="👹",
                                             font=("Arial", int(cs // 2.5)), fill=NEON["enemy"])
                if (i, j) in self.level.treasures:
                    self.canvas.create_text(x1 + cs // 2, y1 + cs // 2 - 8, text="💰",
                                             font=("Arial", int(cs // 2.5)), fill=NEON["treasure"])
                if (i, j) in self.level.portals:
                    self.canvas.create_text(x1 + cs // 2, y1 + cs // 2 + 8, text="🌀",
                                             font=("Arial", int(cs // 2.5)), fill=NEON["portal"])
                if base != 9:
                    self.canvas.create_text(x1 + 12, y1 + 16, text=str(base),
                                             font=("Arial", max(8, cs // 6)), fill="#08101a")
                if self.level.hjb[i, j] < 1e8:
                    self.canvas.create_text(x2 - 14, y2 - 10, text=f"{self.level.hjb[i, j]:.0f}",
                                             font=("Arial", max(6, cs // 8)), fill="#E0FFFF")

        # Marqueur de Lilith (au lieu de la maison)
        hi, hj = self.level.home
        hx1 = hj * cs
        hy1 = hi * cs
        self.canvas.create_oval(hx1 + cs // 4, hy1 + cs // 4, hx1 + 3 * cs // 4, hy1 + 3 * cs // 4,
                                 outline="#FF69B4", width=4, fill="")
        self.canvas.create_text(hx1 + cs // 2, hy1 + cs // 2, text="👩 Lilith",
                                 font=("Arial", int(cs // 3)), fill="#FFB6C1")

    def _draw_player(self, player: Player) -> None:
        i, j = player.pos
        cs = self.cell_size
        x = j * cs + cs // 2
        y = i * cs + cs // 2
        for cid in player.canvas_ids:
            self.canvas.delete(cid)
        oval = self.canvas.create_oval(x - cs // 3, y - cs // 3, x + cs // 3, y + cs // 3,
                                        fill=player.color, outline="", stipple="gray50")
        text = self.canvas.create_text(x, y, text=player.skin, font=("Arial", int(cs // 2.2)))
        player.canvas_ids = [oval, text]

    def _update_ui(self) -> None:
        for bar, player in zip(self.energy_bars, self.players):
            bar.set(player.energy / ENERGIE_MAX)
        if len(self.players) == 2 and self.game_active:
            self.turn_label.configure(text=f"➤ Tour de {self.players[self.current_player_idx].name}")
        else:
            self.turn_label.configure(text="")
        if self.players:
            pos = self.players[self.current_player_idx].pos
            val = self.level.hjb[pos]
            self.hjb_label.configure(text=f"HJB à ta position : {val:.1f}")

    # ------------------------------------------------------------------
    # Gestion des déplacements
    # ------------------------------------------------------------------
    def on_key_press(self, event) -> None:
        if not self.game_active or self.animating:
            return
        key = event.keysym
        player = self.players[self.current_player_idx]
        if len(self.players) == 1:
            moves = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1),
                     "w": (-1, 0), "s": (1, 0), "a": (0, -1), "d": (0, 1)}
        else:
            if self.current_player_idx == 0:  # Don Juan utilise les flèches
                moves = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}
            else:  # Pedro utilise WASD
                moves = {"w": (-1, 0), "s": (1, 0), "a": (0, -1), "d": (0, 1)}
        if key in moves:
            di, dj = moves[key]
            ni, nj = player.pos[0] + di, player.pos[1] + dj
            if 0 <= ni < self.level.size and 0 <= nj < self.level.size:
                self._try_move(player, (ni, nj))

    def _try_move(self, player: Player, new_pos) -> None:
        if self.level.grid[new_pos] == 9:
            self._flash_text("Bloqué !", "#FF8A8A", player)
            return

        cost = int(self.level.cost_at(new_pos))
        if player.energy - cost <= 0:
            player.energy = 0
            self._update_ui()
            self._check_game_over()
            return

        old_pos = player.pos
        player.energy -= cost
        player.pos = new_pos

        if new_pos in self.level.treasures:
            self.level.treasures.remove(new_pos)
            player.energy = min(ENERGIE_MAX, player.energy + 3)
            self._flash_text("+3⚡", "#FFE55C", player)
            self._draw_map()

        if new_pos in self.level.portals:
            exit_pos = self.level.portals[new_pos]
            player.pos = exit_pos
            self._flash_text("🌀 Whoosh!", "#C5A3FF", player)

        self._animate_move(player, old_pos, player.pos)
        self._draw_player(player)
        self._update_ui()

        if player.pos == self.level.home:
            self._win(player)
            return

        if len(self.players) == 2 and self.game_active:
            self.current_player_idx = 1 - self.current_player_idx
            self._update_ui()

    def _animate_move(self, player: Player, old, new) -> None:
        self.animating = True
        oi, oj = old
        ni, nj = new
        cs = self.cell_size
        dx = (nj - oj) * cs / 10
        dy = (ni - oi) * cs / 10
        for _step in range(10):
            for cid in player.canvas_ids:
                self.canvas.move(cid, dx, dy)
            self.update()
            time.sleep(0.02)
        self.animating = False

    def _flash_text(self, msg: str, color: str, player: Player = None) -> None:
        if player is None:
            player = self.players[0]
        i, j = player.pos
        cs = self.cell_size
        x = j * cs + cs // 2
        y = i * cs + cs // 2 - 25
        tid = self.canvas.create_text(x, y, text=msg, font=("Arial", 12, "bold"), fill=color)

        def fade(step: int = 0) -> None:
            if step > 10:
                self.canvas.delete(tid)
                return
            self.canvas.move(tid, 0, -1)
            self.after(40, lambda: fade(step + 1))

        fade()

    # ------------------------------------------------------------------
    # Déplacement automatique (HJB)
    # ------------------------------------------------------------------
    def auto_move(self) -> None:
        if not self.game_active or self.animating:
            return
        player = self.players[self.current_player_idx]
        i, j = player.pos
        best = None
        best_val = float("inf")
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < self.level.size and 0 <= nj < self.level.size and self.level.grid[ni, nj] != 9:
                if self.level.hjb[ni, nj] < best_val:
                    best_val = self.level.hjb[ni, nj]
                    best = (ni, nj)
        if (i, j) in self.level.portals:
            exit_pos = self.level.portals[(i, j)]
            if self.level.hjb[exit_pos] < best_val:
                best_val = self.level.hjb[exit_pos]
                best = exit_pos
        if best:
            self._try_move(player, best)
        else:
            self._flash_text("Aucune case sûre !", "#FF8A8A", player)

    # ------------------------------------------------------------------
    # Fin de partie
    # ------------------------------------------------------------------
    def _check_game_over(self) -> None:
        alive_players = [p for p in self.players if p.energy > 0 and not p.won]
        if not alive_players:
            if len(self.players) == 1:
                msg = "Don Juan a épuisé toute son énergie... Lilith reste inaccessible."
            else:
                msg = "Les deux rivaux sont à bout de forces. Personne n'atteint Lilith."
            self._game_over(msg)
        elif len(alive_players) == 1 and len(self.players) == 2:
            self._win(alive_players[0])

    def _win(self, player: Player) -> None:
        player.won = True
        self.game_active = False
        energy_left = player.energy
        level_name = self.level.name
        solo = len(self.players) == 1
        if solo:
            self.scores.update(level_name, energy_left, solo=True)
            if player.name == "Don Juan":
                msg = f"Don Juan a rejoint Lilith avec {energy_left}⚡ ! Il peut désormais... lui déclarer sa flamme ?"
            else:
                msg = "Pedro a rattrapé Don Juan ! Lilith est sauve, pour l'instant..."
        else:
            self.scores.update(level_name, energy_left, solo=False)
            if player.name == "Don Juan":
                msg = f"Don Juan triomphe de Pedro et rejoint Lilith avec {energy_left}⚡ ! L'amour l'emporte."
            else:
                msg = "Pedro a défendu son honneur ! Don Juan est repoussé, Lilith reste avec Pedro."

        self._show_victory_options(player, msg)

    def _show_victory_options(self, player: Player, message: str) -> None:
        dialog = Toplevel(self)
        dialog.title("Victoire !")
        dialog.geometry("400x250")
        dialog.configure(bg="#1E2A3A")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=message, font=("Arial", 14), wraplength=350,
                     text_color="#F4E3B2").pack(pady=20)

        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(expand=True)

        if self.current_level_idx + 1 < len(self.levels):
            ctk.CTkButton(btn_frame, text="Chapitre suivant", font=("Arial", 12),
                          command=lambda: self._next_level(dialog)).pack(pady=5, padx=20, fill="x")
        else:
            ctk.CTkLabel(btn_frame, text="Bravo ! Tu as terminé tous les chapitres.",
                         font=("Arial", 12, "italic")).pack(pady=5)

        ctk.CTkButton(btn_frame, text="Rejouer ce chapitre", font=("Arial", 12),
                      command=lambda: self._replay_level(dialog)).pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(btn_frame, text="Retour au menu", font=("Arial", 12),
                      command=lambda: self._back_to_menu_from_dialog(dialog)).pack(pady=5, padx=20, fill="x")

    def _reset_current_level(self) -> None:
        """Replace les joueurs au départ et redessine la carte du niveau courant."""
        for p in self.players:
            p.pos = self.level.start
            p.energy = ENERGIE_MAX
            p.won = False
        self.current_player_idx = 0
        self.game_active = True
        self.cell_size = min(self.canvas.winfo_width() // self.level.size,
                              self.canvas.winfo_height() // self.level.size)
        self._draw_map()
        for p in self.players:
            self._draw_player(p)
        self._update_ui()
        self.focus_set()

    def _next_level(self, dialog: Toplevel) -> None:
        dialog.destroy()
        self.current_level_idx += 1
        self.level = self.levels[self.current_level_idx]
        self._reset_current_level()

    def _replay_level(self, dialog: Toplevel) -> None:
        dialog.destroy()
        self.level.generate()  # garantit un chemin, nouvelle distribution
        self._reset_current_level()

    def _back_to_menu_from_dialog(self, dialog: Toplevel) -> None:
        dialog.destroy()
        self.back_to_menu()

    def _game_over(self, msg: str) -> None:
        self.game_active = False
        retry = messagebox.askyesno("Game Over", msg + "\n\nVeux-tu réessayer avec une nouvelle carte ?")
        if retry:
            self.level.generate()
            self._reset_current_level()
        else:
            self.back_to_menu()

    def surrender(self) -> None:
        self._game_over("Tu as abandonné... Lilith attendra.")

    # ------------------------------------------------------------------
    # Infobulle au survol
    # ------------------------------------------------------------------
    def on_hover(self, event) -> None:
        cs = self.cell_size
        col = event.x // cs
        row = event.y // cs
        if 0 <= row < self.level.size and 0 <= col < self.level.size:
            cell = (row, col)
            info = f"Position: {cell}\nCoût de base: {self.level.grid[cell]}\nHJB: {self.level.hjb[cell]:.1f}"
            if cell in self.level.enemies:
                info += "\n⚠️ Ennemi (+2)"
            if cell in self.level.treasures:
                info += "\n💰 Trésor (+3⚡)"
            if cell in self.level.portals:
                info += f"\n🌀 Portail vers {self.level.portals[cell]}"
            if self.tooltip_id:
                self.canvas.delete(self.tooltip_id)
            x1 = col * cs + 5
            y1 = row * cs + 5
            self.tooltip_id = self.canvas.create_text(x1, y1, text=info, font=("Arial", 9),
                                                        fill="white", anchor="nw", tags="tooltip")

    # ------------------------------------------------------------------
    # Retour au menu
    # ------------------------------------------------------------------
    def back_to_menu(self) -> None:
        self.game_active = False
        if hasattr(self, "game_frame"):
            self.game_frame.destroy()
        self._build_menu()
