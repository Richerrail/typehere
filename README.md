# TypeHere 🟢

Guide visuel clignotant + injection de texte depuis le terminal vers n'importe quel champ de saisie.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20X11-orange.svg)

## 💡 Pourquoi ce script ?

Oui, **ce script est très utile** ! C'est un outil pratique pour injecter du texte depuis le terminal vers n'importe quel champ de saisie de ton interface graphique. Voici en quoi il peut être utile.

### 🎯 Cas d'usage principaux :

1. **Productivité améliorée** : Tu peux générer/préparer du texte en ligne de commande et l'envoyer directement dans des formulaires, champs de recherche, etc. sans copier-coller manuel.

2. **Automatisation de saisie** : Idéal pour les workflows où tu dois remplir des champs répétitifs (formulaires web, bases de données, etc.).

3. **Guide visuel précis** : La barre verte clignotante te permet de **viser exactement** où tu veux injecter le texte, même si plusieurs champs sont visibles à l'écran.

4. **Raccourcis custom** : Tu peux scripter la génération de texte (dates, templates, données) dans ton terminal et les injecter directement dans n'importe quelle application.

5. **Accessibilité** : Utile pour les personnes qui préfèrent ou ont besoin d'utiliser le terminal plutôt que de naviguer à la souris.

### ⚠️ Limitations :

- ⚙️ Nécessite **X11** (pas de Wayland natif)
- 🔒 Requiert `xdotool` et un environnement Linux
- ⏱️ Délai de 1,5s fixe avant l'injection (mode standard)

## ✨ Fonctionnalités

- **Curseur guide** : Petite barre verticale clignotante et déplaçable à la souris
- **Injection X11** : Envoie du texte + touche Entrée dans n'importe quelle fenêtre via `xdotool`
- **Workflow rapide** : Tape dans le terminal → le texte est injecté là où pointe le guide
- **Personnalisable** : Taille, couleur, vitesse de clignotement, transparence
- **Mode CLI avancé** : Ciblage de fenêtres, macros JSON, support i3wm

## 📦 Prérequis

```bash
sudo apt install xdotool        # Debian/Ubuntu
sudo pacman -S xdotool          # Arch
sudo dnf install xdotool        # Fedora
```

> **Note** : Nécessite un environnement X11 (Wayland non supporté nativement par `xdotool`).

## 🚀 Utilisation rapide

### Mode overlay (version standard)

```bash
python3 type_here.py
```

1. **Déplace** la barre verte sur le champ de texte cible (clic-glissé)
2. **Clique** dans la fenêtre cible pour lui donner le focus
3. **Tape** ton texte dans le terminal, appuie sur **Entrée**
4. Le texte est injecté après un délai de 1,5s (temps de viser)

#### Raccourcis

| Action | Contrôle |
|--------|----------|
| Déplacer le guide | Clic-glissé sur la barre |
| Redimensionner | Molette de la souris |
| Quitter | `Ctrl+C` dans le terminal |

**Exemple en pratique :**

```
$ python3 type_here.py

🟢  Guide actif — Place la barre verte | sur ta cible.
⌨️  Tape ton texte ICI (dans le terminal), touche Entrée pour l'injecter.
🖱️  Clic-glissé pour déplacer  |  Molette pour hauteur  |  Ctrl+C pour quitter

> Bonjour le monde
⏳  Injection dans 1.5s… clique dans la barre de recherche !
✅  Injecté.
```

## ⚙️ Configuration basique

Modifie les constantes en début du fichier `type_here.py` :

```python
CARET_COLOR = "#00FF00"   # Couleur du curseur
CARET_HEIGHT = 22         # Hauteur en pixels
BLINK_MS = 530            # Vitesse de clignotement (ms)
INITIAL_X, INITIAL_Y = 100, 100  # Position initiale
```

## 🔥 Utilisation avancée avec `type_here_v2.py`

`type_here_v2.py` est une version **surpuissante** du script original. Elle permet d'automatiser complètement le processus sans interface graphique.

### Installation en tant que commande globale (optionnel)

```bash
cp type_here_v2.py ~/.local/bin/type_here
chmod +x ~/.local/bin/type_here
# Puis utilise simplement : type_here --help
```

### Commandes principales

#### 1️⃣ Mode overlay amélioré (avec texte pré-rempli)

```bash
# Afficher le guide avec du texte déjà prêt
python3 type_here_v2.py --overlay --type "photo de singe"

# Avec un délai personnalisé pour viser (3 secondes au lieu de 1.5)
python3 type_here_v2.py --overlay --type "recherche google" --delay 3
```

#### 2️⃣ Injection directe sans interface

```bash
# Taper du texte dans la fenêtre active
python3 type_here_v2.py --type "hello world"

# Cibler une fenêtre par sa classe (ex: Firefox, Spotify, Terminal)
python3 type_here_v2.py --class Firefox --type "linux tutorial"

# Cibler par ID de fenêtre exact
python3 type_here_v2.py --id 69206078 --type "texte cible"

# Cibler par titre (partiel) de la fenêtre
python3 type_here_v2.py --title "Terminal" --type "echo 'hello'"
```

#### 3️⃣ Automatisation de touches et clics

```bash
# Appuyer sur Entrée
python3 type_here_v2.py --class Firefox --key Return

# Combos clavier (Ctrl+L, Alt+Tab, etc.)
python3 type_here_v2.py --key "ctrl+l"
python3 type_here_v2.py --key "alt+Tab"

# Cliquer à des coordonnées précises
python3 type_here_v2.py --click 500,300
```

#### 4️⃣ Support i3wm (meilleur focus que xdotool)

```bash
# Utiliser i3-msg pour cibler une fenêtre (plus fiable sous i3wm)
python3 type_here_v2.py --i3 --class Firefox --type "hello"
```

#### 5️⃣ Exécuter une commande puis injecter

```bash
# Ouvrir Firefox, attendre 3 secondes, puis taper
python3 type_here_v2.py --exec "firefox" --delay 3 --type "photo de singe"

# Exécuter une commande sans attendre
python3 type_here_v2.py --exec "sleep 2; firefox" --type "texte"
```

#### 6️⃣ Lister les fenêtres visibles

```bash
# Voir toutes les fenêtres (ID, classe, titre)
python3 type_here_v2.py --list

# Inclure aussi les fenêtres sans nom
python3 type_here_v2.py --list-all
```

#### 7️⃣ Macros JSON (workflows complets)

Créez un fichier `workflow.json` :

```json
[
  { "action": "exec", "command": "firefox" },
  { "action": "wait", "seconds": 3 },
  { "action": "focus", "class": "Firefox" },
  { "action": "type", "text": "github.com" },
  { "action": "key", "key": "Return" },
  { "action": "wait", "seconds": 2 },
  { "action": "click", "x": 400, "y": 300 }
]
```

Puis exécutez :

```bash
python3 type_here_v2.py --macro workflow.json
```

**Actions supportées dans les macros :**
- `focus` : { "action": "focus", "class": "Firefox" }
- `activate` : { "action": "activate", "class": "Firefox" }
- `type` : { "action": "type", "text": "hello" }
- `key` : { "action": "key", "key": "Return" }
- `click` : { "action": "click", "x": 100, "y": 200 }
- `exec` : { "action": "exec", "command": "firefox" }
- `wait` : { "action": "wait", "seconds": 1.5 }
- `i3_focus` : { "action": "i3_focus", "class": "Firefox" }

### Exemples pratiques complets

#### 🔍 Recherche automatique

```bash
# Chercher "TypeHere" sur GitHub sans quitter le terminal
python3 type_here_v2.py \
  --exec "firefox" \
  --delay 3 \
  --class Firefox \
  --type "github.com/richerrail/typehere" \
  --key Return
```

#### 📝 Remplissage de formulaire

```bash
python3 type_here_v2.py --macro form_workflow.json
```

Contenu de `form_workflow.json` :

```json
[
  { "action": "focus", "title": "Formulaire" },
  { "action": "click", "x": 150, "y": 100 },
  { "action": "type", "text": "Jean Dupont" },
  { "action": "key", "key": "Tab" },
  { "action": "type", "text": "jean@example.com" },
  { "action": "key", "key": "Tab" },
  { "action": "type", "text": "Mon message ici" },
  { "action": "click", "x": 400, "y": 400 },
  { "action": "key", "key": "Return" }
]
```

#### 🖥️ Démonstration multilingue

```bash
python3 type_here_v2.py --overlay --type "Bonjour 🌍 مرحبا" --delay 2
```

### Détection et diagnostique

```bash
# Voir quels outils sont disponibles (X11 ou Wayland ?)
python3 type_here_v2.py --help-functions

# Exemple de sortie :
# Détecté sur cette machine : x11
# xdotool : ✅
# i3-msg  : ❌
```

## 🎥 Démo vidéo

[![Regarder la démo sur YouTube](https://img.shields.io/badge/YouTube-Regarder%20la%20démo-red?style=flat-square&logo=youtube)](https://youtu.be/wFCT-J5g2ps)

Voir la vidéo pour une démonstration du fonctionnement complet en action.

## 📁 Structure

```
type_here.py      # Script principal simple (overlay + stdin)
type_here_v2.py   # Version avancée (CLI, macros, i3wm, etc.)
README.md         # Ce fichier
LICENSE           # Licence MIT
```

## 🛠️ Dépendances

- Python ≥ 3.8
- `tkinter` (généralement inclus avec Python)
- `xdotool` (mandatory)
- `i3-msg` (optionnel, pour i3wm)
- `xprop` (optionnel, meilleure détection de fenêtres)

## 🐛 Dépannage

### "xdotool : command not found"
```bash
sudo apt install xdotool
```

### Aucune fenêtre trouvée
```bash
# Vérifiez quelle est la classe exacte de votre fenêtre
python3 type_here_v2.py --list
```

### L'injection ne fonctionne pas sous Wayland
TypeHere nécessite X11. Si vous êtes sous Wayland :
```bash
# Vérifiez votre serveur graphique
echo $XDG_SESSION_TYPE
# Passez à X11 ou attendez une version Wayland
```

## 💡 Cas d'usage avancés

### 1. Génération dynamique de texte
```bash
# Injecter la date/heure actuelle
python3 type_here_v2.py --class Firefox --type "$(date '+%Y-%m-%d %H:%M')"
```

### 2. Lecture depuis un fichier
```bash
# Injecter le contenu d'un fichier
python3 type_here_v2.py --class Firefox --type "$(cat message.txt)"
```

### 3. Piping avec d'autres commandes
```bash
# Générer du texte via des scripts et l'injecter
python3 type_here_v2.py --class Firefox --type "$(echo 'hello' | tr 'a-z' 'A-Z')"
```

### 4. Boucles d'automatisation
```bash
# Injecter plusieurs lignes
for word in "apple" "banana" "cherry"; do
  python3 type_here_v2.py --class MyApp --type "$word"
  python3 type_here_v2.py --key Return
  sleep 0.5
done
```

## 📝 Licence

[MIT](LICENSE) — Libre d'utilisation, de modification et de distribution.

---

**Questions ?** Ouvrez une issue ou consultez la [démo vidéo](https://youtu.be/wFCT-J5g2ps) !
