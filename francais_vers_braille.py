#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Traducteur Français → Braille (8 pins).
Convention : 0 = down, 1 = up
Pins : [pin0, pin1, pin2, pin3, pin4, pin5, pin6, pin7]
Lancer sans argument : ouvre l'interface graphique. Avec --cli : mode terminal.
"""
import re
import subprocess
import sys
try:
    import tkinter as tk
    from tkinter import ttk, font as tkfont, filedialog
    _GUI_DISPONIBLE = True
except ImportError:
    _GUI_DISPONIBLE = False

# Glisser-déposer de fichiers (optionnel)
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    _DND_DISPONIBLE = True
except ImportError:
    TkinterDnD = None
    _DND_DISPONIBLE = False

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
_COULEUR_SURLIGNAGE = "#f4d03f"  # mot actuel en jaune dans la page de texte


def _mettre_a_jour_detail_mot(mot: str, frame_detail: tk.Frame) -> None:
    """Remplit le tableau détail pour un seul mot (caractère → pins → Braille)."""
    for w in frame_detail.winfo_children():
        w.destroy()
    if not mot:
        return
    resultats = phrase_vers_braille(mot)
    ttk.Label(frame_detail, text="Car.", style="Table.TLabel").grid(row=0, column=0, padx=8, pady=2, sticky="w")
    ttk.Label(frame_detail, text="Pins (8)", style="Table.TLabel").grid(row=0, column=1, padx=8, pady=2, sticky="w")
    ttk.Label(frame_detail, text="Braille", style="Table.TLabel").grid(row=0, column=2, padx=8, pady=2, sticky="w")
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


def main_gui() -> None:
    root = (TkinterDnD.Tk() if _DND_DISPONIBLE else tk.Tk)()
    root.title("Traducteur Français → Braille")
    root.geometry("620x640")
    root.minsize(500, 500)
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
    titre_font = tkfont.Font(family="Helvetica", size=16, weight="bold")
    ttk.Label(root, text="Traducteur Français → Braille (8 pins)", font=titre_font).pack(pady=(main_pad, 4))
    ttk.Label(root, text="Ouvrez un fichier .txt puis parcourez mot par mot avec Prev / Next.").pack(pady=(0, main_pad))

    # État : fichier chargé, liste de mots, positions, index courant
    state = {"words": [], "word_positions": [], "current_index": 0, "file_content": ""}

    # --- Zone d'import (masquée une fois le fichier chargé) ---
    frame_import = ttk.Frame(root)
    frame_import.pack(fill="x", padx=main_pad, pady=(0, 8))

    # --- Zone fichier : clic ouvre le sélecteur ; drop charge le fichier ---
    def _charger_fichier(path: str) -> None:
        if not path or not path.strip():
            return
        path = path.strip().strip("{}")  # tkinterdnd2 envoie parfois {chemin}
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                state["file_content"] = f.read()
        except OSError:
            label_fichier.config(text="Erreur lors de la lecture du fichier.")
            return
        state["word_positions"] = [(m.start(), m.end()) for m in re.finditer(r"\S+", state["file_content"])]
        state["words"] = [state["file_content"][s:e] for s, e in state["word_positions"]]
        state["current_index"] = 0
        label_fichier.config(text=path.split("/")[-1].split("\\")[-1] or path)
        preview_text.config(state=tk.NORMAL)
        preview_text.delete("1.0", tk.END)
        preview_text.insert("1.0", state["file_content"])
        preview_text.config(state=tk.DISABLED)
        _update_current_word()
        # Cacher la zone d'import une fois le texte chargé
        frame_import.pack_forget()

    def _ouvrir_fichier():
        path = filedialog.askopenfilename(
            title="Ouvrir un fichier texte",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
        )
        if path:
            _charger_fichier(path)

    def _on_drop(event):
        # tkinterdnd2 : event.data = "{path}" ou "{path1} {path2}"
        data = getattr(event, "data", "") or ""
        for part in data.replace("}", " ").replace("{", " ").split():
            part = part.strip()
            if part.lower().endswith(".txt") or part:
                _charger_fichier(part)
                break

    frame_zone_fichier = tk.Frame(frame_import, bg=_COULEUR_PANEAU, padx=20, pady=16)
    frame_zone_fichier.pack(fill="x", pady=(0, 8))
    label_zone = ttk.Label(frame_zone_fichier, text="Glissez-déposez un fichier .txt ici ou cliquez pour parcourir", cursor="hand2")
    label_zone.pack(pady=(0, 4))
    label_fichier = ttk.Label(frame_zone_fichier, text="Aucun fichier ouvert")
    label_fichier.pack()
    for w in (frame_zone_fichier, label_zone, label_fichier):
        w.bind("<Button-1>", lambda e: _ouvrir_fichier())
    if _DND_DISPONIBLE:
        try:
            root.drop_target_register(DND_FILES)
            root.dnd_bind("<<Drop>>", _on_drop)
        except Exception:
            pass
    ttk.Button(frame_import, text="Ouvrir un fichier .txt", command=_ouvrir_fichier).pack(pady=(0, 4))

    # --- Page de texte (tout le texte avec mot actuel en surlignage jaune) ---
    _placeholder_texte = "Aucun fichier ouvert. Glissez-déposez un fichier .txt ici ou cliquez sur « Ouvrir un fichier .txt » ci-dessus."
    ttk.Label(root, text="Texte :").pack(anchor="w", padx=main_pad, pady=(8, 2))
    frame_preview = ttk.Frame(root)
    frame_preview.pack(fill="both", expand=True, padx=main_pad, pady=(0, 4))
    preview_text = tk.Text(
        frame_preview, wrap=tk.WORD, height=22, bg="#ffffff", fg="#000000",
        insertbackground="#000000", font=("Helvetica", 12), state=tk.NORMAL,
        padx=12, pady=12
    )
    preview_text.insert("1.0", _placeholder_texte)
    preview_text.config(state=tk.DISABLED)
    preview_text.tag_configure("highlight", background=_COULEUR_SURLIGNAGE)
    scroll_preview = ttk.Scrollbar(frame_preview)
    scroll_preview.pack(side=tk.RIGHT, fill="y")
    preview_text.pack(side=tk.LEFT, fill="both", expand=True)
    preview_text.config(yscrollcommand=scroll_preview.set)
    scroll_preview.config(command=preview_text.yview)

    # --- Mot actuel + Braille + Prev / Next ---
    ttk.Label(root, text="Mot actuel (traduction Braille) :").pack(anchor="w", padx=main_pad, pady=(8, 2))
    frame_mot = ttk.Frame(root)
    frame_mot.pack(fill="x", padx=main_pad, pady=(0, 4))
    label_mot_actuel = ttk.Label(frame_mot, text="—", font=("Helvetica", 12, "bold"))
    label_mot_actuel.pack(side=tk.LEFT, padx=(0, 12))
    label_compteur = ttk.Label(frame_mot, text="")
    label_compteur.pack(side=tk.LEFT)
    braille_font = tkfont.Font(family="Helvetica", size=28)
    label_braille = ttk.Label(root, text="", font=braille_font)
    label_braille.pack(anchor="w", padx=main_pad, pady=(0, 8))

    frame_btns = ttk.Frame(root)
    frame_btns.pack(fill="x", padx=main_pad, pady=(0, 8))
    btn_prev = ttk.Button(frame_btns, text="← Prev")
    btn_next = ttk.Button(frame_btns, text="Next →")
    tk.Frame(frame_btns, width=1).pack(side=tk.LEFT, expand=True)
    btn_prev.pack(side=tk.LEFT, padx=4)
    btn_next.pack(side=tk.LEFT, padx=4)
    tk.Frame(frame_btns, width=1).pack(side=tk.LEFT, expand=True)

    def _update_current_word():
        words = state["words"]
        idx = state["current_index"]
        # Mise à jour surlignage dans la prévisualisation
        preview_text.tag_remove("highlight", "1.0", tk.END)
        if words and 0 <= idx < len(words):
            start, end = state["word_positions"][idx]
            preview_text.config(state=tk.NORMAL)
            start_idx = f"1.0+{start}c"
            end_idx = f"1.0+{end}c"
            preview_text.tag_add("highlight", start_idx, end_idx)
            preview_text.see(start_idx)
            preview_text.config(state=tk.DISABLED)
            mot = words[idx]
            label_mot_actuel.config(text=mot or "—")
            resultats = phrase_vers_braille(mot)
            visuel = ""
            for car, pins in zip(mot, resultats):
                visuel += pins_vers_unicode_braille(pins) if pins is not None else "?"
            label_braille.config(text=visuel)
            _mettre_a_jour_detail_mot(mot, frame_detail)
            label_compteur.config(text=f"Mot {idx + 1} / {len(words)}")
        else:
            label_mot_actuel.config(text="—")
            label_braille.config(text="")
            label_compteur.config(text="")
            for w in frame_detail.winfo_children():
                w.destroy()
        btn_prev.state(["!disabled"] if idx > 0 else ["disabled"])
        btn_next.state(["!disabled"] if idx < len(words) - 1 and words else ["disabled"])

    def _prev():
        if state["current_index"] > 0:
            state["current_index"] -= 1
            _update_current_word()

    def _next():
        if state["current_index"] < len(state["words"]) - 1:
            state["current_index"] += 1
            _update_current_word()

    btn_prev.config(command=_prev)
    btn_next.config(command=_next)

    # --- CTA : Ouvrir l'alphabet Braille ---
    def _ouvrir_alphabet():
        win = tk.Toplevel(root)
        win.title("Alphabet Braille")
        win.configure(bg=_COULEUR_FOND)
        win.geometry("400x420")
        f = ttk.Frame(win, padding=12)
        f.pack(fill="both", expand=True)
        ttk.Label(f, text="Lettres et symboles Braille (8 points)", font=("Helvetica", 12, "bold")).grid(row=0, column=0, columnspan=4, pady=(0, 12))
        row, col = 1, 0
        for lettre in "abcdefghijklmnopqrstuvwxyz ":
            lbl = "esp." if lettre == " " else lettre
            ttk.Label(f, text=lbl, width=4).grid(row=row, column=col, padx=4, pady=2)
            pins = BRAILLE.get(lettre)
            if pins:
                sym = pins_vers_unicode_braille(pins)
                ttk.Label(f, text=sym, style="Braille.TLabel", font=("Helvetica", 20)).grid(row=row, column=col + 1, padx=4, pady=2)
            col += 2
            if col >= 4:
                col = 0
                row += 1
        ttk.Label(f, text="Accents : à â é è ê ë î ï ô ù û ü ç").grid(row=row + 1, column=0, columnspan=4, pady=12)

    # --- CTA : Épeler le mot actuel avec son (une lettre = un son) ---
    def _epeler_avec_son():
        words = state["words"]
        idx = state["current_index"]
        if not words or idx < 0 or idx >= len(words):
            return
        mot = words[idx]
        if not mot:
            return

        def _dire_lettres():
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

    # --- Barre des CTA en bas ---
    frame_cta = ttk.Frame(root)
    frame_cta.pack(fill="x", padx=main_pad, pady=(4, 8))
    ttk.Button(frame_cta, text="Ouvrir l'alphabet Braille", command=_ouvrir_alphabet).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(frame_cta, text="Épeler le mot (son)", command=_epeler_avec_son).pack(side=tk.LEFT)

    # --- Tableau détail (caractères du mot actuel) ---
    ttk.Label(root, text="Détail (caractère → pins → Braille) :").pack(anchor="w", padx=main_pad, pady=(8, 2))
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

    frame_detail.bind("<Configure>", _on_frame_configure)
    canvas.bind("<Configure>", lambda e: (canvas.itemconfig(canvas_window, width=e.width), canvas.configure(scrollregion=canvas.bbox("all"))))
    canvas.bind("<MouseWheel>", lambda evt: canvas.yview_scroll(int(-1 * (evt.delta / 120)), "units"))

    btn_prev.state(["disabled"])
    btn_next.state(["disabled"])

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
