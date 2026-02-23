#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Traducteur Français → Braille (8 pins).
Convention : 0 = down, 1 = up
Pins : [pin0, pin1, pin2, pin3, pin4, pin5, pin6, pin7]
Lancer sans argument : ouvre l'interface graphique. Avec --cli : mode terminal.
"""
try:
    import tkinter as tk
    from tkinter import ttk, font as tkfont
    _GUI_DISPONIBLE = True
except ImportError:
    _GUI_DISPONIBLE = False

# Mapping Braille standard (Perkins / BANA). Grille 6 points :
#   dot1 dot4     → indices 0, 4
#   dot2 dot5     → indices 1, 5
#   dot3 dot6     → indices 2, 6   (index 3 et 7 réservés 8-dot)
BRAILLE_LETTRES = {
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
    'u': [1, 0, 1, 0, 0, 0, 1, 0],   # dots 1,3,6
    'v': [1, 1, 1, 0, 0, 0, 1, 0],   # dots 1,2,3,6
    'w': [0, 1, 0, 0, 1, 1, 1, 0],   # dots 2,4,5,6
    'x': [1, 0, 1, 0, 1, 0, 1, 0],   # dots 1,3,4,6
    'y': [1, 0, 1, 0, 1, 1, 1, 0],   # dots 1,3,4,5,6 (6-dot) / 1,3,5,6,7 (8-dot liblouis ⠽)
    'z': [1, 0, 1, 0, 0, 1, 1, 0],   # dots 1,3,5,6
}

# Espace = toutes les pins à 0
BRAILLE_LETTRES[' '] = [0, 0, 0, 0, 0, 0, 0, 0]

# Ponctuation Braille standard (dots 1-6 → indices 0,1,2,4,5,6)
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

# Dictionnaire unifié : lettres + espace + ponctuation
# Lettres accentuées françaises courantes (Braille français)
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


def lettre_vers_braille(lettre: str) -> list[int] | None:
    """Retourne la liste des 8 pins pour une lettre, ou None si inconnue."""
    if not lettre:
        return BRAILLE[' ']
    c = lettre[0] if len(lettre) > 1 else lettre
    # Lettres en minuscule pour la recherche
    if c.isalpha():
        c = c.lower()
    return BRAILLE.get(c)


def phrase_vers_braille(phrase: str) -> list[list[int]]:
    """Retourne la liste des 8 pins pour chaque caractère de la phrase."""
    return [lettre_vers_braille(c) for c in phrase]


def pins_vers_unicode_braille(pins: list[int]) -> str:
    """
    Convertit une liste de 8 pins en caractère Braille Unicode (visuel).
    Convention Unicode : dot1=0x01, dot2=0x02, dot3=0x04, dot4=0x08, dot5=0x10, dot6=0x20,
    dot7=0x40, dot8=0x80. Nos indices 0,1,2,4,5,6 → dots 1-6 ; 3,7 → dots 7-8.
    """
    if not pins or len(pins) < 7:
        return chr(0x2800)  # cellule vide
    # Ordre des bits Unicode : dots 1,2,3,4,5,6,7,8 → indices 0,1,2,4,5,6,3,7
    value = (
        pins[0] * 0x01 + pins[1] * 0x02 + pins[2] * 0x04
        + pins[4] * 0x08 + pins[5] * 0x10 + pins[6] * 0x20
        + (pins[3] if len(pins) > 3 else 0) * 0x40
        + (pins[7] if len(pins) > 7 else 0) * 0x80
    )
    return chr(0x2800 + value)


def main():
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


# --- Interface graphique ---
_COULEUR_FOND = "#1a1b26"
_COULEUR_PANEAU = "#24283b"
_COULEUR_TEXTE = "#c0caf5"
_COULEUR_ACCENT = "#7aa2f7"
_COULEUR_BRAILLE_BG = "#414868"
_COULEUR_ENTREE = "#2d3047"


def _traduire_et_afficher(entree_var: tk.StringVar, frame_detail: tk.Frame, label_braille: tk.Label) -> None:
    """Met à jour l'affichage Braille et le tableau détail selon le contenu de entree_var."""
    # Vider le détail
    for w in frame_detail.winfo_children():
        w.destroy()
    entree = entree_var.get().strip()
    if not entree:
        label_braille.config(text="")
        return
    resultats = phrase_vers_braille(entree)
    visuel_braille = ""
    for car, pins in zip(entree, resultats):
        visuel_braille += pins_vers_unicode_braille(pins) if pins is not None else "?"
    label_braille.config(text=visuel_braille)

    # En-tête du tableau
    ttk.Label(frame_detail, text="Car.", style="Table.TLabel").grid(row=0, column=0, padx=8, pady=2, sticky="w")
    ttk.Label(frame_detail, text="Pins (8)", style="Table.TLabel").grid(row=0, column=1, padx=8, pady=2, sticky="w")
    ttk.Label(frame_detail, text="Braille", style="Table.TLabel").grid(row=0, column=2, padx=8, pady=2, sticky="w")
    for i, (car, pins) in enumerate(zip(entree, resultats)):
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


def main_gui() -> None:
    root = tk.Tk()
    root.title("Traducteur Français → Braille")
    root.geometry("520x480")
    root.minsize(400, 360)
    root.configure(bg=_COULEUR_FOND)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure(".", background=_COULEUR_FOND, foreground=_COULEUR_TEXTE)
    style.configure("TLabel", background=_COULEUR_FOND, foreground=_COULEUR_TEXTE)
    style.configure("TFrame", background=_COULEUR_FOND)
    style.configure("Table.TLabel", background=_COULEUR_PANEAU, foreground=_COULEUR_TEXTE)
    style.configure("Braille.TLabel", background=_COULEUR_PANEAU, foreground=_COULEUR_ACCENT)
    style.configure("TButton", background=_COULEUR_ACCENT, foreground=_COULEUR_FOND)
    style.map("TButton", background=[("active", _COULEUR_TEXTE)])

    main_pad = 16
    # Titre
    titre_font = tkfont.Font(family="Helvetica", size=16, weight="bold")
    ttk.Label(root, text="Traducteur Français → Braille (8 pins)", font=titre_font).pack(pady=(main_pad, 8))
    ttk.Label(root, text="Saisissez du texte pour voir le rendu en Braille et le détail des pins.").pack(pady=(0, main_pad))

    # Champ de saisie
    frame_entree = ttk.Frame(root)
    frame_entree.pack(fill="x", padx=main_pad, pady=(0, 8))
    entree_var = tk.StringVar()
    entree_var.trace_add("write", lambda *_: _traduire_et_afficher(entree_var, frame_detail, label_braille))
    entree = ttk.Entry(root, textvariable=entree_var, width=50)
    entree.pack(fill="x", padx=main_pad, pady=(0, main_pad))
    entree.focus_set()

    # Rendu Braille (visuel)
    ttk.Label(root, text="Rendu Braille :").pack(anchor="w", padx=main_pad, pady=(8, 2))
    braille_font = tkfont.Font(family="Helvetica", size=28)
    label_braille = ttk.Label(root, text="", font=braille_font)
    label_braille.pack(anchor="w", padx=main_pad, pady=(0, main_pad))

    # Zone défilable pour le détail
    canvas_container = ttk.Frame(root)
    canvas_container.pack(fill="both", expand=True, padx=main_pad, pady=(0, main_pad))
    canvas = tk.Canvas(canvas_container, bg=_COULEUR_FOND, highlightthickness=0)
    scrollbar = ttk.Scrollbar(canvas_container)
    scrollbar.pack(side=tk.RIGHT, fill="y")
    canvas.pack(side=tk.LEFT, fill="both", expand=True)
    scrollbar.config(command=canvas.yview)
    canvas.config(yscrollcommand=scrollbar.set)

    frame_detail = tk.Frame(canvas, bg=_COULEUR_PANEAU, padx=12, pady=10)
    canvas_window = canvas.create_window((0, 0), window=frame_detail, anchor="nw")

    def _on_frame_configure(_event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(canvas_window, width=canvas.winfo_width())

    def _on_canvas_configure(e):
        canvas.itemconfig(canvas_window, width=e.width)

    frame_detail.bind("<Configure>", _on_frame_configure)
    canvas.bind("<Configure>", lambda e: (canvas.itemconfig(canvas_window, width=e.width), canvas.configure(scrollregion=canvas.bbox("all"))))

    def _scroll_canvas(evt):
        canvas.yview_scroll(int(-1 * (evt.delta / 120)), "units")
    canvas.bind("<MouseWheel>", _scroll_canvas)

    root.mainloop()


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
