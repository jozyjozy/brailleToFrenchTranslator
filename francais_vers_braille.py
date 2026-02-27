#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Traducteur Français → Braille (8 pins)
=====================================

Interface graphique pour traduire du texte français en Braille 8 points.
- Ouvrir un fichier .txt (glisser-déposer ou bouton)
- Navigation mot par mot (Prev / Next) avec pagination type livre
- Affichage du mot actuel en Braille (pins + symbole Unicode)
- Alphabet Braille complet (popup)
- Épellation vocale du mot actuel (TTS)

Convention : 0 = pin down, 1 = pin up
Pins : [pin0, pin1, pin2, pin3, pin4, pin5, pin6, pin7]

Usage :
  python3 francais_vers_braille.py       # Interface graphique
  python3 francais_vers_braille.py --cli # Mode terminal
"""

# ============================================================================
# IMPORTS
# ============================================================================
import re
import subprocess
import sys

try:
    import tkinter as tk
    from tkinter import ttk, font as tkfont, filedialog
    _GUI_DISPONIBLE = True
except ImportError:
    _GUI_DISPONIBLE = False

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    _DND_DISPONIBLE = True
except ImportError:
    TkinterDnD = None
    _DND_DISPONIBLE = False


# ============================================================================
# TABLES BRAILLE (8 POINTS)
# ============================================================================
# Mapping Braille standard (Perkins / BANA). Grille 6 points :
#   dot1 dot4     → indices 0, 4
#   dot2 dot5     → indices 1, 5
#   dot3 dot6     → indices 2, 6   (index 3 et 7 réservés 8-dot)

BRAILLE_LETTRES = {
    # Lettres a-j (première série)
    'a': [1, 0, 0, 0, 0, 0, 0, 0],
    'b': [1, 1, 0, 0, 0, 0, 0, 0],
    'c': [1, 0, 0, 0, 1, 0, 0, 0],
    'd': [1, 0, 0, 0, 1, 1, 0, 0],
    'e': [1, 0, 0, 0, 0, 1, 0, 0],   # dots 1,5
    'f': [1, 1, 0, 0, 1, 0, 0, 0],   # dots 1,2,4
    'g': [1, 1, 0, 0, 1, 1, 0, 0],   # dots 1,2,4,5
    'h': [1, 1, 0, 0, 0, 1, 0, 0],   # dots 1,2,5
    'i': [0, 1, 0, 0, 1, 0, 0, 0],   # dots 2,4
    'j': [0, 1, 0, 0, 1, 1, 0, 0],   # dots 2,4,5
    
    # Lettres k-t (deuxième série, ajout dot 3)
    'k': [1, 0, 1, 0, 0, 0, 0, 0],   # dots 1,3
    'l': [1, 1, 1, 0, 0, 0, 0, 0],   # dots 1,2,3
    'm': [1, 0, 1, 0, 1, 0, 0, 0],   # dots 1,3,4
    'n': [1, 0, 1, 0, 1, 1, 0, 0],   # dots 1,3,4,5
    'o': [1, 0, 1, 0, 0, 1, 0, 0],   # dots 1,3,5
    'p': [1, 1, 1, 0, 1, 0, 0, 0],   # dots 1,2,3,4
    'q': [1, 1, 1, 0, 1, 1, 0, 0],   # dots 1,2,3,4,5
    'r': [1, 1, 1, 0, 0, 1, 0, 0],   # dots 1,2,3,5
    's': [0, 1, 1, 0, 1, 0, 0, 0],   # dots 2,3,4
    't': [0, 1, 1, 0, 1, 1, 0, 0],   # dots 2,3,4,5
    
    # Lettres u-z (troisième série, ajout dot 6)
    'u': [1, 0, 1, 0, 0, 0, 1, 0],   # dots 1,3,6
    'v': [1, 1, 1, 0, 0, 0, 1, 0],   # dots 1,2,3,6
    'w': [0, 1, 0, 0, 1, 1, 1, 0],   # dots 2,4,5,6
    'x': [1, 0, 1, 0, 1, 0, 1, 0],   # dots 1,3,4,6
    'y': [1, 0, 1, 0, 1, 1, 1, 0],   # dots 1,3,4,5,6 (6-dot) / 1,3,5,6,7 (8-dot liblouis ⠽)
    'z': [1, 0, 1, 0, 0, 1, 1, 0],   # dots 1,3,5,6
}

# Espace
BRAILLE_LETTRES[' '] = [0, 0, 0, 0, 0, 0, 0, 0]

# --- Ponctuation ---
BRAILLE_PONCTUATION = {
    '.': [0, 1, 0, 0, 1, 1, 0, 0],   # point (2,5,6)
    ',': [0, 1, 0, 0, 0, 1, 0, 0],   # virgule (2,6)
    '?': [0, 1, 1, 0, 0, 1, 0, 0],   # point d'interrogation (2,3,6)
    '!': [0, 1, 1, 0, 1, 0, 0, 0],   # point d'exclamation (2,3,5)
    "'": [0, 0, 1, 0, 0, 0, 0, 0],   # apostrophe (3)
    ':': [0, 1, 0, 0, 1, 0, 0, 0],   # deux-points (2,5)
    ';': [0, 1, 1, 0, 1, 0, 0, 0],   # point-virgule (2,3,5)
    '-': [0, 0, 1, 0, 0, 1, 0, 0],   # tiret (3,6)
    '(': [1, 1, 1, 0, 1, 1, 0, 0],   # parenthèse ouvrante (1,2,3,5,6)
    ')': [0, 1, 1, 1, 1, 1, 0, 0],   # parenthèse fermante (2,3,4,5,6)
    '"': [0, 1, 1, 0, 0, 1, 0, 0],   # guillemet (2,3,6)
    '/': [0, 0, 1, 0, 1, 0, 1, 0],   # slash (3,4,6)
    '…': [0, 1, 0, 0, 1, 0, 0, 0],   # points de suspension (même que :)
}

# --- Lettres accentuées françaises ---
BRAILLE_ACCENTS = {
    'à': [1, 0, 0, 0, 0, 0, 0, 0],   # comme a (ou spécifique selon norme)
    'â': [1, 0, 0, 0, 0, 0, 0, 0],
    'é': [1, 0, 0, 0, 0, 1, 0, 0],
    'è': [1, 0, 0, 0, 0, 1, 0, 0],
    'ê': [1, 0, 0, 0, 0, 1, 0, 0],
    'ë': [1, 0, 0, 0, 0, 1, 0, 0],
    'î': [0, 1, 0, 0, 1, 0, 0, 0],
    'ï': [0, 1, 0, 0, 1, 0, 0, 0],
    'ô': [1, 0, 1, 0, 0, 1, 0, 0],
    'ù': [1, 0, 1, 0, 0, 0, 1, 0],
    'û': [1, 0, 1, 0, 0, 0, 1, 0],
    'ü': [1, 0, 1, 0, 0, 0, 1, 0],
    'ç': [1, 1, 1, 1, 0, 1, 0, 0],   # c cédille (1,2,3,4,6)
}

# Dictionnaire unifié : lettres + espace + ponctuation + accents
BRAILLE = {**BRAILLE_LETTRES, **BRAILLE_PONCTUATION, **BRAILLE_ACCENTS}


# ============================================================================
# FONCTIONS DE TRADUCTION
# ============================================================================

def lettre_vers_braille(lettre: str) -> list[int] | None:
    """
    Retourne la liste des 8 pins pour une lettre donnée.
    
    Args:
        lettre: Caractère à traduire (lettre, ponctuation, accent, espace)
    
    Returns:
        Liste de 8 entiers (0 ou 1) représentant les pins Braille, ou None si inconnu
    """
    if not lettre:
        return BRAILLE[' ']
    
    c = lettre[0] if len(lettre) > 1 else lettre
    if c.isalpha():
        c = c.lower()
    
    return BRAILLE.get(c)


def phrase_vers_braille(phrase: str) -> list[list[int]]:
    """
    Traduit une phrase complète en Braille.
    
    Args:
        phrase: Texte à traduire
    
    Returns:
        Liste de listes de 8 pins (une par caractère)
    """
    return [lettre_vers_braille(c) for c in phrase]


def pins_vers_unicode_braille(pins: list[int]) -> str:
    """
    Convertit une liste de 8 pins en caractère Braille Unicode (visuel).
    
    Convention Unicode : dot1=0x01, dot2=0x02, dot3=0x04, dot4=0x08, dot5=0x10, dot6=0x20,
    dot7=0x40, dot8=0x80. Nos indices 0,1,2,4,5,6 → dots 1-6 ; 3,7 → dots 7-8.
    
    Args:
        pins: Liste de 8 entiers (0 ou 1)
    
    Returns:
        Caractère Unicode Braille (U+2800 à U+28FF)
    """
    if not pins or len(pins) < 7:
        return chr(0x2800)
    
    value = (
        pins[0] * 0x01 + pins[1] * 0x02 + pins[2] * 0x04
        + pins[4] * 0x08 + pins[5] * 0x10 + pins[6] * 0x20
        + (pins[3] if len(pins) > 3 else 0) * 0x40
        + (pins[7] if len(pins) > 7 else 0) * 0x80
    )
    return chr(0x2800 + value)



# ============================================================================
# MODE TERMINAL (CLI)
# ============================================================================

def main():
    """Mode terminal : saisie interactive pour tester la traduction."""
    print("=== Traducteur Français → Braille (8 pins) ===\n")
    print("Convention : 0 = down, 1 = up")
    print("Format sortie : [pin0, pin1, pin2, pin3, pin4, pin5, pin6, pin7]\n")

    while True:
        entree = input("Entrez une phrase ou une lettre (vide + Entrée ou 'quitter' pour quitter) : ").strip()
        if not entree or entree.lower() == 'quitter':
            print("Au revoir.")
            break
        # Traiter la phrase caractère par caractère
        resultats = phrase_vers_braille(entree)
        print()
        # Ligne visuelle Braille (toute la phrase en caractères Unicode)
        visuel_braille = ""
        for car, pins in zip(entree, resultats):
            if pins is not None:
                visuel_braille += pins_vers_unicode_braille(pins)
            else:
                visuel_braille += "?"
        if visuel_braille:
            print("  Rendu Braille :  " + visuel_braille + "\n")

        for i, (car, pins) in enumerate(zip(entree, resultats)):
            if pins is not None:
                aff = repr(car) if car == ' ' else car
                symbole = pins_vers_unicode_braille(pins)
                print(f"  {aff:>4}  →  {pins}  │  {symbole}")
            else:
                print(f"  {car!r:>4}  →  (non supporté, ignoré)")
        print()


# --- Interface graphique : thème « bibliothèque » (bois marron + pages jaunies) ---
# Police unique pour tout l’interface (style livre)
_FONT_FAMILLE = "Georgia"
# Fond principal (ton bois / étagère)
_COULEUR_FOND = "#e2d9c8"
# Panneaux (blanc cassé jauni, type papier ancien)
_COULEUR_PANEAU = "#f5f0e6"
# Texte principal (marron foncé)
_COULEUR_TEXTE = "#3d2c1f"
# Texte secondaire
_COULEUR_TEXTE_SECONDAIRE = "#5c4a3d"
# Boutons (marron bois)
_COULEUR_ACCENT = "#6b5344"
# Survol des boutons (marron plus foncé)
_COULEUR_ACCENT_HOVER = "#4a3c30"
# Zone de détail / tableau (papier légèrement jauni)
_COULEUR_TABLEAU = "#f0ebe0"
# Surlignage du mot actuel (ambre / jaune doux)
_COULEUR_SURLIGNAGE = "#f5e6c8"
# Page de livre : papier crème
_COULEUR_PAGE = "#faf6f0"
_COULEUR_TEXTE_LIVRE = "#3d2c1f"
# Bordure de page (marron clair)
_COULEUR_BORDURE_PAGE = "#c4b59a"
# Couverture vide (cuir / ouvrage ancien)
_COULEUR_COUVERTURE_CUIR = "#6b4423"
_COULEUR_TEXTE_COUVERTURE = "#c9b896"
# Texte sur boutons (crème pour contraste sur marron)
_COULEUR_BOUTON_TEXTE = "#faf5eb"

MOTS_PAR_PAGE = 120  # Nombre de mots par page


# ============================================================================
# HELPERS INTERFACE GRAPHIQUE
# ============================================================================

def _mettre_a_jour_detail_mot(mot: str, frame_detail: tk.Frame) -> None:
    """
    Remplit le tableau détail pour un seul mot (caractère → pins → Braille).
    
    Args:
        mot: Mot à décomposer
        frame_detail: Frame Tkinter où afficher le tableau
    """
    # Effacer le contenu précédent
    for w in frame_detail.winfo_children():
        w.destroy()
    
    if not mot:
        return
    
    # Traduire le mot en Braille
    resultats = phrase_vers_braille(mot)
    
    # En-têtes du tableau
    ttk.Label(frame_detail, text="Car.", style="Table.TLabel").grid(row=0, column=0, padx=8, pady=2, sticky="w")
    ttk.Label(frame_detail, text="Pins (8)", style="Table.TLabel").grid(row=0, column=1, padx=8, pady=2, sticky="w")
    ttk.Label(frame_detail, text="Braille", style="Table.TLabel").grid(row=0, column=2, padx=8, pady=2, sticky="w")
    
    # Lignes du tableau (une par caractère)
    for i, (car, pins) in enumerate(zip(mot, resultats)):
        r = i + 1
        aff_car = repr(car) if car == " " else car
        ttk.Label(frame_detail, text=aff_car, style="Table.TLabel").grid(row=r, column=0, padx=8, pady=1, sticky="w")
        
        if pins is not None:
            pin_str = str(pins)
            symbole = pins_vers_unicode_braille(pins)
            ttk.Label(frame_detail, text=pin_str, style="Table.TLabel").grid(row=r, column=1, padx=8, pady=1, sticky="w")
            ttk.Label(frame_detail, text=symbole, style="Braille.TLabel").grid(row=r, column=2, padx=8, pady=1, sticky="w")
        else:
            ttk.Label(frame_detail, text="(non supporté)", style="Table.TLabel").grid(row=r, column=1, columnspan=2, padx=8, pady=1, sticky="w")



# ============================================================================
# INTERFACE GRAPHIQUE PRINCIPALE
# ============================================================================

def main_gui() -> None:
    """Lance l'interface graphique (fenêtre principale)."""
    # --- Fenêtre principale ---
    root = (TkinterDnD.Tk() if _DND_DISPONIBLE else tk.Tk)()
    root.title("Traducteur Français → Braille")
    root.geometry("620x640")
    root.minsize(500, 500)
    root.configure(bg=_COULEUR_FOND)

    # --- Styles ttk ---
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(".", background=_COULEUR_FOND, foreground=_COULEUR_TEXTE, font=(_FONT_FAMILLE, 10))
    style.configure("TLabel", background=_COULEUR_FOND, foreground=_COULEUR_TEXTE, font=(_FONT_FAMILLE, 10))
    style.configure("TFrame", background=_COULEUR_FOND)
    style.configure("Table.TLabel", background=_COULEUR_TABLEAU, foreground=_COULEUR_TEXTE, font=(_FONT_FAMILLE, 10))
    style.configure("Braille.TLabel", background=_COULEUR_TABLEAU, foreground=_COULEUR_TEXTE, font=(_FONT_FAMILLE, 11))
    style.configure("TButton", background=_COULEUR_ACCENT, foreground=_COULEUR_BOUTON_TEXTE, font=(_FONT_FAMILLE, 10))
    style.map("TButton", background=[("active", _COULEUR_ACCENT_HOVER)], foreground=[("active", _COULEUR_BOUTON_TEXTE), ("disabled", _COULEUR_BOUTON_TEXTE)])
    # Boutons Prev/Next : texte blanc forcé (certains thèmes l’affichent en gris)
    style.configure("Nav.TButton", background=_COULEUR_ACCENT, foreground=_COULEUR_BOUTON_TEXTE, font=(_FONT_FAMILLE, 10))
    style.map("Nav.TButton", background=[("active", _COULEUR_ACCENT_HOVER)], foreground=[("active", _COULEUR_BOUTON_TEXTE), ("disabled", "#c4b59a")])

    main_pad = 16

    # ========================================================================
    # ZONE DÉFILABLE (PETITS ÉCRANS)
    # ========================================================================
    main_canvas = tk.Canvas(root, bg=_COULEUR_FOND, highlightthickness=0)
    main_scrollbar = ttk.Scrollbar(root)
    main_scrollbar.pack(side=tk.RIGHT, fill="y")
    main_canvas.pack(side=tk.LEFT, fill="both", expand=True)
    main_canvas.configure(yscrollcommand=main_scrollbar.set)
    main_scrollbar.configure(command=main_canvas.yview)
    content_frame = ttk.Frame(main_canvas)
    content_win = main_canvas.create_window((0, 0), window=content_frame, anchor="nw")
    
    def _on_content_configure(_e=None):
        """Met à jour la région de défilement quand le contenu change."""
        main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        main_canvas.itemconfig(content_win, width=main_canvas.winfo_width())
    
    def _main_scroll(evt):
        """Gère le défilement à la molette."""
        main_canvas.yview_scroll(int(-1 * (evt.delta / 120)), "units")
    
    content_frame.bind("<Configure>", _on_content_configure)
    main_canvas.bind("<Configure>", lambda e: (main_canvas.itemconfig(content_win, width=e.width), main_canvas.configure(scrollregion=main_canvas.bbox("all"))))
    main_canvas.bind("<MouseWheel>", _main_scroll)
    content_frame.bind("<MouseWheel>", _main_scroll)

    # ========================================================================
    # TITRE ET INSTRUCTIONS
    # ========================================================================
    titre_font = tkfont.Font(family=_FONT_FAMILLE, size=16, weight="bold")
    ttk.Label(content_frame, text="Traducteur Français → Braille (8 pins)", font=titre_font).pack(pady=(main_pad, 4))
    ttk.Label(content_frame, text="Ouvrez un fichier .txt puis parcourez mot par mot avec Prev / Next.").pack(pady=(0, main_pad))

    # ========================================================================
    # ÉTAT DE L'APPLICATION
    # ========================================================================
    state = {
        "words": [],           # Liste des mots du fichier
        "word_positions": [],  # Positions (start, end) de chaque mot dans le texte
        "current_index": 0,    # Index du mot actuel
        "current_page": -1,    # Numéro de page courante
        "file_content": ""     # Contenu complet du fichier
    }

    # ========================================================================
    # ZONE D'IMPORT DE FICHIER (masquée après chargement)
    # ========================================================================
    frame_import = ttk.Frame(content_frame)
    frame_import.pack(fill="x", padx=main_pad, pady=(0, 8))

    def _charger_fichier(path: str) -> None:
        """Charge un fichier texte, extrait les mots et met à jour l'interface."""
        if not path or not path.strip():
            return
        path = path.strip().strip("{}")  # tkinterdnd2 envoie parfois {chemin}
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                state["file_content"] = f.read()
        except OSError:
            label_fichier.config(text="Erreur lors de la lecture du fichier.")
            return
        
        # Extraire les mots et leurs positions
        state["word_positions"] = [(m.start(), m.end()) for m in re.finditer(r"\S+", state["file_content"])]
        state["words"] = [state["file_content"][s:e] for s, e in state["word_positions"]]
        state["current_index"] = 0
        
        # Mettre à jour l'interface
        label_fichier.config(text=path.split("/")[-1].split("\\")[-1] or path)
        preview_text.config(state=tk.NORMAL)
        preview_text.delete("1.0", tk.END)
        _build_page_texte()
        preview_text.config(state=tk.DISABLED)
        _update_current_word()
        
        # Masquer la zone d'import
        frame_import.pack_forget()

    def _ouvrir_fichier():
        """Ouvre une boîte de dialogue pour sélectionner un fichier .txt."""
        path = filedialog.askopenfilename(
            title="Ouvrir un fichier texte",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
        )
        if path:
            _charger_fichier(path)

    def _on_drop(event):
        """Gère le glisser-déposer de fichiers (tkinterdnd2)."""
        data = getattr(event, "data", "") or ""
        for part in data.replace("}", " ").replace("{", " ").split():
            part = part.strip()
            if part.lower().endswith(".txt") or part:
                _charger_fichier(part)
                break

    # Zone de dépôt / clic pour ouvrir un fichier
    frame_zone_fichier = tk.Frame(frame_import, bg=_COULEUR_PANEAU, padx=20, pady=16)
    frame_zone_fichier.pack(fill="x", pady=(0, 8))
    label_zone = ttk.Label(frame_zone_fichier, text="Glissez-déposez un fichier .txt ici ou cliquez pour parcourir", cursor="hand2")
    label_zone.pack(pady=(0, 4))
    label_fichier = ttk.Label(frame_zone_fichier, text="Aucun fichier ouvert")
    label_fichier.pack()
    
    # Clic pour ouvrir le sélecteur de fichiers
    for w in (frame_zone_fichier, label_zone, label_fichier):
        w.bind("<Button-1>", lambda e: _ouvrir_fichier())
    
    # Activer le glisser-déposer si disponible
    if _DND_DISPONIBLE:
        try:
            root.drop_target_register(DND_FILES)
            root.dnd_bind("<<Drop>>", _on_drop)
        except Exception:
            pass
    
    ttk.Button(frame_import, text="Ouvrir un fichier .txt", command=_ouvrir_fichier).pack(pady=(0, 4))

    # --- Page de livre (apparence d’une page : papier crème, police serif, marges) ---
    _placeholder_texte = "Aucun fichier ouvert. Glissez-déposez un fichier .txt ici ou cliquez sur « Ouvrir un fichier .txt » ci-dessus."
    ttk.Label(content_frame, text="Texte :").pack(anchor="w", padx=main_pad, pady=(8, 2))
    # Cadre double page : page courante (gauche) + page suivante (droite) ; centré, sans scroll
    _page_largeur_car = 50
    _page_hauteur_lignes = 16
    frame_page = tk.Frame(content_frame, bg=_COULEUR_FOND, padx=main_pad, pady=4)
    frame_page.pack(fill="x", expand=False)
    frame_page_centre = tk.Frame(frame_page, bg=_COULEUR_FOND)
    frame_page_centre.pack(expand=True)
    # Viewport (canvas) pour l’animation de tour de page : le contenu glisse horizontalement
    _viewport_w = 720
    _viewport_h = 380
    canvas_viewport = tk.Canvas(frame_page_centre, bg=_COULEUR_FOND, highlightthickness=0, width=_viewport_w, height=_viewport_h)
    canvas_viewport.pack()
    frame_preview = tk.Frame(canvas_viewport, bg=_COULEUR_BORDURE_PAGE, padx=3, pady=3)
    canvas_page_win = canvas_viewport.create_window(0, 0, window=frame_preview, anchor="nw")
    _page_rest_pos = [0, 0]  # Position centrée de repos (x, y)

    def _center_page_in_viewport():
        """
        Centre la page dans le viewport.
        Calcule et applique les coordonnées (x, y) pour centrer frame_preview dans canvas_viewport.
        """
        root.update_idletasks()
        w = frame_preview.winfo_reqwidth()
        h = frame_preview.winfo_reqheight()
        vw = canvas_viewport.winfo_width() or _viewport_w
        vh = canvas_viewport.winfo_height() or _viewport_h
        _page_rest_pos[0] = max(0, (vw - w) // 2)
        _page_rest_pos[1] = max(0, (vh - h) // 2)
        canvas_viewport.coords(canvas_page_win, _page_rest_pos[0], _page_rest_pos[1])

    canvas_viewport.bind("<Configure>", lambda e: _center_page_in_viewport())
    root.after(100, _center_page_in_viewport)
    
    # Widget Text pour afficher la page courante
    _font_livre = (_FONT_FAMILLE, 11)
    frame_page_gauche = tk.Frame(frame_preview, bg=_COULEUR_COUVERTURE_CUIR)
    frame_page_gauche.pack(fill="y", expand=False)
    preview_text = tk.Text(
        frame_page_gauche, wrap=tk.WORD, width=_page_largeur_car, height=_page_hauteur_lignes,
        bg=_COULEUR_COUVERTURE_CUIR, fg=_COULEUR_TEXTE_COUVERTURE,
        insertbackground=_COULEUR_TEXTE_LIVRE,
        font=_font_livre, state=tk.NORMAL,
        padx=22, pady=18,
        spacing1=3, spacing2=2, spacing3=4,
        relief=tk.FLAT, highlightthickness=0,
        borderwidth=0
    )
    preview_text.insert("1.0", _placeholder_texte)
    preview_text.config(state=tk.DISABLED)
    preview_text.tag_configure("highlight", background=_COULEUR_SURLIGNAGE)
    preview_text.pack(fill="y", expand=False)
    
    # Labels de pagination (style livre : « — 3 — » et « Page 3 / 12 »)
    frame_pagination = ttk.Frame(frame_page)
    frame_pagination.pack(fill="x", pady=(4, 8))
    label_pagination_centre = ttk.Label(frame_pagination, text="", font=(_FONT_FAMILLE, 10))
    label_pagination_centre.pack()
    label_pagination_texte = ttk.Label(frame_pagination, text="", font=(_FONT_FAMILLE, 9))
    label_pagination_texte.pack(pady=(2, 0))
    
    # Aller à une page directement
    frame_go_to_page = ttk.Frame(frame_pagination)
    frame_go_to_page.pack(pady=(6, 0))
    ttk.Label(frame_go_to_page, text="Aller à la page :", font=(_FONT_FAMILLE, 9)).pack(side=tk.LEFT, padx=(0, 4))
    entry_go_page = ttk.Entry(frame_go_to_page, width=5, font=(_FONT_FAMILLE, 10))
    entry_go_page.pack(side=tk.LEFT, padx=2)
    btn_go_page = ttk.Button(frame_go_to_page, text="Aller", style="TButton")
    btn_go_page.pack(side=tk.LEFT, padx=2)

    # ========================================================================
    # MOT ACTUEL + BRAILLE + NAVIGATION (PREV / NEXT)
    # ========================================================================
    ttk.Label(content_frame, text="Mot actuel (traduction Braille) :").pack(anchor="w", padx=main_pad, pady=(8, 2))
    
    # Mot actuel + compteur
    frame_mot = ttk.Frame(content_frame)
    frame_mot.pack(fill="x", padx=main_pad, pady=(0, 4))
    label_mot_actuel = ttk.Label(frame_mot, text="—", font=(_FONT_FAMILLE, 12, "bold"))
    label_mot_actuel.pack(side=tk.LEFT, padx=(0, 12))
    label_compteur = ttk.Label(frame_mot, text="")
    label_compteur.pack(side=tk.LEFT)
    
    # Symbole Braille du mot actuel
    braille_font = tkfont.Font(family=_FONT_FAMILLE, size=28)
    label_braille = ttk.Label(content_frame, text="", font=braille_font)
    label_braille.pack(anchor="w", padx=main_pad, pady=(0, 8))

    # Boutons Prev / Next (centrés)
    frame_btns = ttk.Frame(content_frame)
    frame_btns.pack(fill="x", padx=main_pad, pady=(0, 8))
    btn_prev = ttk.Button(frame_btns, text="← Prev", style="Nav.TButton")
    btn_next = ttk.Button(frame_btns, text="Next →", style="Nav.TButton")
    tk.Frame(frame_btns, width=1).pack(side=tk.LEFT, expand=True)
    btn_prev.pack(side=tk.LEFT, padx=4)
    btn_next.pack(side=tk.LEFT, padx=4)
    tk.Frame(frame_btns, width=1).pack(side=tk.LEFT, expand=True)

    # ========================================================================
    # LOGIQUE DE MISE À JOUR (PAGE + MOT + ANIMATION)
    # ========================================================================
    
    def _build_page_texte():
        """
        Construit le contenu de la page courante (MOTS_PAR_PAGE mots).
        Met à jour le widget Text et les labels de pagination.
        """
        words = state["words"]
        idx = state["current_index"]
        preview_text.config(state=tk.NORMAL)
        preview_text.delete("1.0", tk.END)
        
        if not words:
            # Aucun fichier : afficher placeholder avec style "couverture cuir"
            preview_text.insert("1.0", _placeholder_texte)
            frame_page_gauche.config(bg=_COULEUR_COUVERTURE_CUIR)
            preview_text.config(bg=_COULEUR_COUVERTURE_CUIR, fg=_COULEUR_TEXTE_COUVERTURE)
            label_pagination_centre.config(text="")
            label_pagination_texte.config(text="")
            state["current_page"] = -1
        else:
            # Fichier chargé : style "papier crème"
            frame_page_gauche.config(bg=_COULEUR_PAGE)
            preview_text.config(bg=_COULEUR_PAGE, fg=_COULEUR_TEXTE_LIVRE)
            
            # Calculer la page courante et les mots à afficher
            page = idx // MOTS_PAR_PAGE
            state["current_page"] = page
            total_pages = max(1, (len(words) + MOTS_PAR_PAGE - 1) // MOTS_PAR_PAGE)
            start_w = page * MOTS_PAR_PAGE
            end_w = min(start_w + MOTS_PAR_PAGE, len(words))
            page_words = words[start_w:end_w]
            
            # Insérer le texte de la page
            preview_text.insert("1.0", " ".join(page_words))
            
            # Mettre à jour la pagination
            label_pagination_centre.config(text=f"— {page + 1} —")
            label_pagination_texte.config(text=f"Page {page + 1} / {total_pages}  ({len(page_words)} mots)")
        
        preview_text.config(state=tk.DISABLED)

    def _update_current_word():
        words = state["words"]
        idx = state["current_index"]
        preview_text.tag_remove("highlight", "1.0", tk.END)
        if words and 0 <= idx < len(words):
            page = idx // MOTS_PAR_PAGE
            start_w = page * MOTS_PAR_PAGE
            end_w = min(start_w + MOTS_PAR_PAGE, len(words))
            page_words = words[start_w:end_w]
            # Changer de page si le mot actuel n’est pas sur la page affichée
            if page != state.get("current_page", -1):
                _run_page_turn_animation(1 if page > state.get("current_page", -1) else -1, _apply_current_word_display)
                return
        _apply_current_word_display()

    _page_turn_anim_id = [None]

    def _run_page_turn_animation(direction, on_done):
        """
        Animation de tour de page : glissement horizontal.
        
        Args:
            direction: 1 = page suivante (glisse vers la gauche), -1 = page précédente (glisse vers la droite)
            on_done: Callback à appeler après le changement de contenu (avant phase 2)
        
        Fonctionnement :
            Phase 1 : La page actuelle glisse hors du viewport
            Entre les phases : _build_page_texte() + on_done() pour mettre à jour le contenu
            Phase 2 : La nouvelle page glisse dans le viewport depuis le côté opposé
        """
        _center_page_in_viewport()
        rest_x, rest_y = _page_rest_pos[0], _page_rest_pos[1]
        root.update_idletasks()
        w = max(frame_preview.winfo_reqwidth(), 400)
        steps, delay_ms = 10, 25
        step_out = -(w * direction) // steps
        step_in = -(w * direction) // steps

        def phase1(step=0):
            """Phase 1 : glissement de la page actuelle hors du viewport."""
            if _page_turn_anim_id[0] is not None:
                root.after_cancel(_page_turn_anim_id[0])
            
            if step <= steps:
                canvas_viewport.coords(canvas_page_win, rest_x + step * step_out, rest_y)
                _page_turn_anim_id[0] = root.after(delay_ms, lambda: phase1(step + 1))
            else:
                # Mise à jour du contenu (nouvelle page)
                _build_page_texte()
                on_done()
                # Positionner la nouvelle page hors du viewport (côté opposé)
                canvas_viewport.coords(canvas_page_win, rest_x + (w if direction > 0 else -w), rest_y)
                phase2(0)

        def phase2(step=0):
            """Phase 2 : glissement de la nouvelle page dans le viewport."""
            if _page_turn_anim_id[0] is not None:
                root.after_cancel(_page_turn_anim_id[0])
            
            if step <= steps:
                x0 = rest_x + (w if direction > 0 else -w)
                canvas_viewport.coords(canvas_page_win, x0 + step * step_in, rest_y)
                _page_turn_anim_id[0] = root.after(delay_ms, lambda: phase2(step + 1))
            else:
                # Animation terminée : repositionner au centre
                canvas_viewport.coords(canvas_page_win, rest_x, rest_y)
                _page_turn_anim_id[0] = None

        phase1(0)

    def _apply_current_word_display():
        """
        Applique le surlignage du mot actuel et met à jour les labels.
        Appelé après _build_page_texte() ou directement si pas de changement de page.
        """
        words, idx = state["words"], state["current_index"]
        preview_text.tag_remove("highlight", "1.0", tk.END)
        
        if words and 0 <= idx < len(words):
            page = idx // MOTS_PAR_PAGE
            start_w = page * MOTS_PAR_PAGE
            end_w = min(start_w + MOTS_PAR_PAGE, len(words))
            page_words = words[start_w:end_w]
            idx_in_page = idx - start_w
            
            # Calculer la position du mot dans le texte de la page (en caractères)
            char_start = len(" ".join(page_words[:idx_in_page]))
            char_end = char_start + len(page_words[idx_in_page])
            
            # Surligner le mot actuel dans la page
            preview_text.tag_add("highlight", f"1.0+{char_start}c", f"1.0+{char_end}c")
            preview_text.see(f"1.0+{char_start}c")
            
            # Mettre à jour les labels
            mot = words[idx]
            label_mot_actuel.config(text=mot or "—")
            resultats = phrase_vers_braille(mot)
            visuel = "".join(pins_vers_unicode_braille(p) if p else "?" for p in resultats)
            label_braille.config(text=visuel)
            _mettre_a_jour_detail_mot(mot, frame_detail)
            label_compteur.config(text=f"Mot {idx + 1} / {len(words)}")
        else:
            # Aucun mot : réinitialiser l'affichage
            label_mot_actuel.config(text="—")
            label_braille.config(text="")
            label_compteur.config(text="")
            for c in list(frame_detail.winfo_children()):
                c.destroy()
        
        # État des boutons Prev/Next
        btn_prev.state(["!disabled"] if state["current_index"] > 0 else ["disabled"])
        btn_next.state(["!disabled"] if state["current_index"] < len(state["words"]) - 1 and state["words"] else ["disabled"])

    def _prev():
        """Passe au mot précédent."""
        if state["current_index"] > 0:
            state["current_index"] -= 1
            _update_current_word()

    def _next():
        """Passe au mot suivant."""
        if state["current_index"] < len(state["words"]) - 1:
            state["current_index"] += 1
            _update_current_word()

    btn_prev.config(command=_prev)
    btn_next.config(command=_next)

    def _aller_a_la_page():
        """Va directement à la page dont le numéro est saisi (sans animation)."""
        words = state["words"]
        if not words:
            return
        try:
            p = int(entry_go_page.get().strip())
        except ValueError:
            return
        total_pages = max(1, (len(words) + MOTS_PAR_PAGE - 1) // MOTS_PAR_PAGE)
        if p < 1 or p > total_pages:
            return
        state["current_index"] = (p - 1) * MOTS_PAR_PAGE
        _build_page_texte()
        _apply_current_word_display()

    btn_go_page.config(command=_aller_a_la_page)
    entry_go_page.bind("<Return>", lambda e: _aller_a_la_page())

    # ========================================================================
    # CTA : OUVRIR L'ALPHABET BRAILLE
    # ========================================================================
    
    def _ouvrir_alphabet():
        """Ouvre une fenêtre popup affichant tous les caractères Braille supportés."""
        win = tk.Toplevel(root)
        win.title("Alphabet Braille")
        win.configure(bg=_COULEUR_FOND)
        win.geometry("520x420")
        ttk.Label(win, text="Lettres, ponctuation et accents Braille (8 points)", font=(_FONT_FAMILLE, 12, "bold")).pack(pady=(12, 8))
        
        # Zone défilable pour l'alphabet
        frame_canvas = ttk.Frame(win)
        frame_canvas.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        canvas = tk.Canvas(frame_canvas, bg=_COULEUR_FOND, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame_canvas)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        canvas.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.config(command=canvas.yview)
        canvas.config(yscrollcommand=scrollbar.set)
        
        f = ttk.Frame(canvas, padding=4)
        canvas_window = canvas.create_window((0, 0), window=f, anchor="nw")
        
        def _on_frame_configure(_e=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
        
        def _on_canvas_configure(e):
            canvas.itemconfig(canvas_window, width=e.width)
        
        def _scroll_alphabet(evt):
            canvas.yview_scroll(int(-1 * (evt.delta / 120)), "units")
        
        f.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.bind("<MouseWheel>", _scroll_alphabet)
        
        # Tous les caractères supportés (ordre : a-z, espace, ponctuation, accents)
        lettres_base = "abcdefghijklmnopqrstuvwxyz "
        ponctuation = ".,?!':;-()\"/…"
        accents = "àâéèêëîïôùûüç"
        tous_caracteres = list(lettres_base) + [c for c in ponctuation] + [c for c in accents]
        
        # En-têtes du tableau (2 colonnes de caractères)
        ttk.Label(f, text="Car.", font=(_FONT_FAMILLE, 10, "bold")).grid(row=0, column=0, padx=3, pady=2)
        ttk.Label(f, text="Braille", font=(_FONT_FAMILLE, 10, "bold")).grid(row=0, column=1, padx=3, pady=2)
        ttk.Label(f, text="Car.", font=(_FONT_FAMILLE, 10, "bold")).grid(row=0, column=2, padx=3, pady=2)
        ttk.Label(f, text="Braille", font=(_FONT_FAMILLE, 10, "bold")).grid(row=0, column=3, padx=3, pady=2)
        
        # Remplir le tableau (2 caractères par ligne)
        row, col = 1, 0
        for lettre in tous_caracteres:
            # Affichage spécial pour certains caractères
            if lettre == " ":
                lbl = "esp."
            elif lettre == "'":
                lbl = "'"
            elif lettre == '"':
                lbl = '"'
            elif lettre == "…":
                lbl = "…"
            else:
                lbl = lettre
            
            ttk.Label(f, text=lbl, width=3).grid(row=row, column=col, padx=3, pady=2)
            pins = BRAILLE.get(lettre)
            if pins:
                sym = pins_vers_unicode_braille(pins)
                ttk.Label(f, text=sym, style="Braille.TLabel", font=(_FONT_FAMILLE, 18)).grid(row=row, column=col + 1, padx=3, pady=2)
            
            # Passer à la colonne suivante (2 caractères par ligne)
            col += 2
            if col >= 4:
                col = 0
                row += 1

    # ========================================================================
    # CTA : ÉPELER LE MOT (TTS PAR LETTRE)
    # ========================================================================
    
    def _epeler_avec_son():
        """Épelle le mot actuel lettre par lettre avec synthèse vocale (TTS)."""
        words = state["words"]
        idx = state["current_index"]
        if not words or idx < 0 or idx >= len(words):
            return
        mot = words[idx]
        if not mot:
            return

        def _dire_lettres():
            """Thread pour prononcer chaque lettre du mot."""
            for c in mot:
                lettre = c if c.isalpha() or c in "àâéèêëîïôùûüç" else " "
                try:
                    if sys.platform == "darwin":
                        subprocess.run(["say", "-v", "Thomas", lettre], check=False, timeout=2, capture_output=True)
                    elif sys.platform == "win32":
                        subprocess.run(["powershell", "-Command", f"Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak('{lettre}')"], check=False, timeout=2, capture_output=True)
                    else:
                        subprocess.run(["espeak", "-v", "fr", lettre], check=False, timeout=2, capture_output=True)
                except Exception:
                    pass

        import threading
        threading.Thread(target=_dire_lettres, daemon=True).start()

    # ========================================================================
    # BARRE DES CTA (CENTRÉE)
    # ========================================================================
    frame_cta = ttk.Frame(content_frame)
    frame_cta.pack(fill="x", padx=main_pad, pady=(4, 8))
    tk.Frame(frame_cta, width=1).pack(side=tk.LEFT, expand=True)
    ttk.Button(frame_cta, text="Ouvrir l'alphabet Braille", command=_ouvrir_alphabet).pack(side=tk.LEFT, padx=4)
    ttk.Button(frame_cta, text="Épeler le mot (son)", command=_epeler_avec_son).pack(side=tk.LEFT, padx=4)
    tk.Frame(frame_cta, width=1).pack(side=tk.LEFT, expand=True)

    # ========================================================================
    # TABLEAU DÉTAIL (CARACTÈRES DU MOT ACTUEL)
    # ========================================================================
    ttk.Label(content_frame, text="Détail (caractère → pins → Braille) :").pack(anchor="w", padx=main_pad, pady=(8, 2))
    
    # Zone défilable pour le tableau détail
    canvas_container = ttk.Frame(content_frame)
    canvas_container.pack(fill="both", expand=True, padx=main_pad, pady=(0, main_pad))
    canvas = tk.Canvas(canvas_container, bg=_COULEUR_FOND, highlightthickness=0)
    scrollbar = ttk.Scrollbar(canvas_container)
    scrollbar.pack(side=tk.RIGHT, fill="y")
    canvas.pack(side=tk.LEFT, fill="both", expand=True)
    scrollbar.config(command=canvas.yview)
    canvas.config(yscrollcommand=scrollbar.set)
    frame_detail = tk.Frame(canvas, bg=_COULEUR_TABLEAU, padx=12, pady=10)
    canvas_window = canvas.create_window((0, 0), window=frame_detail, anchor="nw")

    def _on_frame_configure(_event=None):
        """Met à jour la région de défilement du tableau détail."""
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(canvas_window, width=canvas.winfo_width())

    frame_detail.bind("<Configure>", _on_frame_configure)
    canvas.bind("<Configure>", lambda e: (canvas.itemconfig(canvas_window, width=e.width), canvas.configure(scrollregion=canvas.bbox("all"))))
    canvas.bind("<MouseWheel>", lambda evt: canvas.yview_scroll(int(-1 * (evt.delta / 120)), "units"))

    # ========================================================================
    # INITIALISATION ET LANCEMENT
    # ========================================================================
    
    # État initial : boutons désactivés (aucun fichier)
    btn_prev.state(["disabled"])
    btn_next.state(["disabled"])

    # Lancement de l'application
    root.mainloop()


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    import sys
    if "--cli" in sys.argv or not _GUI_DISPONIBLE:
        if not _GUI_DISPONIBLE and "--cli" not in sys.argv:
            print("tkinter non disponible : lancement en mode terminal.")
            print("Pour ouvrir la fenêtre graphique, utilisez un Python avec tkinter, par ex. :")
            print("  python3.13 francais_vers_braille.py")
        main()
    else:
        main_gui()
