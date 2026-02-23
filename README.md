# Traducteur Français → Braille (8 pins)

Script Python qui convertit du texte français en **patterns Braille 8 pins**, au format liste de valeurs binaires (pin down/up). Utile pour piloter une plage Braille rafraîchissable, un embosseur ou tout dispositif à 8 broches.

## Prérequis

- **Python 3.7+** (aucune dépendance externe)

## Installation

Aucune. Cloner ou télécharger le dossier et lancer le script.

## Utilisation

```bash
python3 francais_vers_braille.py
```

- Saisir une **phrase** ou une **lettre**, puis Entrée.
- Le script affiche, pour chaque caractère, sa sortie Braille au format `[pin0, pin1, …, pin7]`.
- Pour quitter : entrée vide ou `q`.

### Exemple

```
Entrez une phrase ou une lettre (vide + Entrée ou 'q' pour quitter) : Bonjour

     B  →  [1, 1, 0, 0, 0, 0, 0, 0]
     o  →  [1, 0, 1, 0, 0, 1, 0, 0]
     n  →  [1, 0, 1, 0, 1, 1, 0, 0]
     j  →  [0, 1, 0, 0, 1, 1, 0, 0]
     o  →  [1, 0, 1, 0, 0, 1, 0, 0]
     u  →  [1, 0, 1, 0, 0, 0, 1, 0]
     r  →  [1, 1, 1, 0, 0, 1, 0, 0]
```

## Convention des pins

- **0** = pin down (point non levé)  
- **1** = pin up (point levé)

Chaque caractère est représenté par une liste de **8 entiers** :  
`[pin0, pin1, pin2, pin3, pin4, pin5, pin6, pin7]`.

Correspondance avec la grille Braille standard (6 points) :

| Grille Braille | Index dans la liste |
|----------------|----------------------|
| point 1 (haut gauche)  | 0 |
| point 2 (milieu gauche) | 1 |
| point 3 (bas gauche)   | 2 |
| point 4 (haut droite)  | 4 |
| point 5 (milieu droite) | 5 |
| point 6 (bas droite)   | 6 |

Les indices **3** et **7** sont réservés pour une extension 8 points (ex. liblouis).

## Caractères supportés

- **Lettres** : a–z (majuscules converties en minuscules pour le Braille)
- **Espace** : `[0, 0, 0, 0, 0, 0, 0, 0]`
- **Ponctuation** : `.` `,` `?` `!` `'` `:` `;` `-` `(` `)` `"` `/` `…`
- **Accents français** : à â é è ê ë î ï ô ù û ü **ç**

Les caractères non reconnus sont signalés et ignorés dans la sortie.

## Utilisation en module

```python
from francais_vers_braille import lettre_vers_braille, phrase_vers_braille

# Une lettre
pins = lettre_vers_braille("a")   # → [1, 0, 0, 0, 0, 0, 0, 0]

# Toute une phrase (liste de listes)
liste_pins = phrase_vers_braille("Salut")
# → [[0,1,1,0,1,0,0,0], [1,0,0,0,0,0,0,0], ...]
```

## Références

- Alphabet Braille standard : [Perkins – How the braille alphabet works](https://www.perkins.org/how-the-braille-alphabet-works/)
- Convention 8 points (y, etc.) : compatible avec **liblouis**

## Licence

Libre d’utilisation et de modification.
