# TypeHere 🟢

Guide visuel clignotant + injection de texte depuis le terminal vers n'importe quel champ de saisie.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20X11-orange.svg)

## 💡 Pourquoi ce script ?

Oui, **ce script est très utile** ! C'est un outil pratique pour injecter du texte depuis le terminal vers n'importe quel champ de saisie de ton interface graphique. Voici en quoi il peut être utile :

### 🎯 Cas d'usage principaux :

1. **Productivité améliorée** : Tu peux générer/préparer du texte en ligne de commande et l'envoyer directement dans des formulaires, champs de recherche, etc. sans copier-coller manuel.

2. **Automatisation de saisie** : Idéal pour les workflows où tu dois remplir des champs répétitifs (formulaires web, bases de données, etc.).

3. **Guide visuel précis** : La barre verte clignotante te permet de **viser exactement** où tu veux injecter le texte, même si plusieurs champs sont visibles à l'écran.

4. **Raccourcis custom** : Tu peux scripter la génération de texte (dates, templates, données) dans ton terminal et les injecter directement dans n'importe quelle application.

5. **Accessibilité** : Utile pour les personnes qui préfèrent ou ont besoin d'utiliser le terminal plutôt que de naviguer à la souris.

### ⚠️ Limitations :

- ⚙️ Nécessite **X11** (pas de Wayland natif)
- 🔒 Requiert `xdotool` et un environnement Linux
- ⏱️ Délai de 1,5s fixe avant l'injection

## ✨ Fonctionnalités

- **Curseur guide** : Petite barre verticale clignotante et déplaçable à la souris
- **Injection X11** : Envoie du texte + touche Entrée dans n'importe quelle fenêtre via `xdotool`
- **Workflow rapide** : Tape dans le terminal → le texte est injecté là où pointe le guide
- **Personnalisable** : Taille, couleur, vitesse de clignotement, transparence

## 📦 Prérequis

```bash
sudo apt install xdotool        # Debian/Ubuntu
sudo pacman -S xdotool          # Arch
sudo dnf install xdotool        # Fedora
```

> **Note** : Nécessite un environnement X11 (Wayland non supporté nativement par `xdotool`).

## 🚀 Utilisation

```bash
python3 type_here.py
```

1. **Déplace** la barre verte sur le champ de texte cible (clic-glissé)
2. **Clique** dans la fenêtre cible pour lui donner le focus
3. **Tape** ton texte dans le terminal, appuie sur **Entrée**
4. Le texte est injecté après un délai de 1,5s (temps de viser)

### Raccourcis

| Action | Contrôle |
|--------|----------|
| Déplacer le guide | Clic-glissé sur la barre |
| Redimensionner | Molette de la souris |
| Quitter | `Ctrl+C` dans le terminal |

## ⚙️ Configuration

Modifie les constantes en début de fichier :

```python
CARET_COLOR = "#00FF00"   # Couleur du curseur
CARET_HEIGHT = 22         # Hauteur en pixels
BLINK_MS = 530            # Vitesse de clignotement (ms)
INITIAL_X, INITIAL_Y = 100, 100  # Position initiale
```

## 🖥️ Démo

```
$ python3 type_here.py

🟢  Guide actif — Place la barre verte | sur ta cible.
⌨️  Tape ton texte ICI (dans le terminal), touche Entrée pour l'injecter.
🖱️  Clic-glissé pour déplacer  |  Molette pour hauteur  |  Ctrl+C pour quitter

> Bonjour le monde
⏳  Injection dans 1.5s… clique dans la barre de recherche !
✅  Injecté.
```

## 📁 Structure

```
type_here.py    # Script principal (autonome)
README.md       # Ce fichier
LICENSE         # Licence MIT
```

## 🛠️ Dépendances

- Python ≥ 3.8
- `tkinter` (généralement inclus)
- `xdotool`

## 📝 Licence

[MIT](LICENSE) — Libre d'utilisation, de modification et de distribution.
