#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Traducteur Français → Braille (8 pins).
Convention : 0 = down, 1 = up
Pins : [pin0, pin1, pin2, pin3, pin4, pin5, pin6, pin7]
"""

# Mapping Braille standard : dot numbers 1-6 → indices 0,1,2,4,5,6 (index 3 et 7 non utilisés en 6 points)
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
    'y': [1, 0, 1, 0, 1, 1, 1, 0],   # dots 1,3,5,6,7
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
        for i, (car, pins) in enumerate(zip(entree, resultats)):
            if pins is not None:
                aff = repr(car) if car == ' ' else car
                print(f"  {aff:>4}  →  {pins}")
            else:
                print(f"  {car!r:>4}  →  (non supporté, ignoré)")
        print()


if __name__ == "__main__":
    main()
