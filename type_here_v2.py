#!/usr/bin/env python3
"""
type_here_v2.py — Pont CLI → GUI + overlay visuel pour Linux/X11 et i3wm.

Permet d'injecter du texte, d'appuyer sur des touches ou de cliquer dans une
fenêtre graphique depuis le terminal. Compatible avec les environnements X11,
i3wm, et (partiellement) Wayland.

Usage de base :
    python3 type_here_v2.py --class Firefox --type "hello world"
    python3 type_here_v2.py --title "Terminal" --key Return
    python3 type_here_v2.py --overlay

Auteur : k00 (version améliorée par l'assistant)
Licence : MIT
"""

import argparse
import os
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
from typing import Optional

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
CARET_WIDTH = 2
CARET_HEIGHT = 22
CARET_COLOR = "#00FF00"
BLINK_MS = 530
WIN_W = 4
WIN_H = CARET_HEIGHT + 4
INITIAL_X, INITIAL_Y = 100, 100

# ═══════════════════════════════════════════════════════════════════════════════
# DÉTECTION DE L'ENVIRONNEMENT
# ═══════════════════════════════════════════════════════════════════════════════
def detect_display_server() -> str:
    """
    Détecte le serveur graphique disponible.

    Returns:
        "x11" si la variable DISPLAY est définie et xdotool est présent.
        "wayland" si WAYLAND_DISPLAY est définie (outils comme ydotool/wtype).
        "headless" sinon.
    """
    if os.environ.get("DISPLAY") and shutil.which("xdotool"):
        return "x11"
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    return "headless"


def check_tool(name: str) -> bool:
    """Vérifie si un exécutable est disponible dans le PATH."""
    return shutil.which(name) is not None


def ensure_xdotool() -> None:
    """Quitte avec un message d'erreur si xdotool n'est pas installé."""
    if not check_tool("xdotool"):
        print("❌  'xdotool' est requis. Installe-le : sudo apt install xdotool")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
# OUTILS DE BAS NIVEAU (xdotool)
# ═══════════════════════════════════════════════════════════════════════════════
def run_xdotool(args: list[str], check: bool = False) -> subprocess.CompletedProcess:
    """
    Exécute une commande xdotool avec les arguments donnés.

    Args:
        args: Liste des arguments à passer à xdotool.
        check: Si True, lève une exception en cas d'erreur.

    Returns:
        L'objet CompletedProcess de subprocess.
    """
    return subprocess.run(["xdotool", *args], capture_output=True, text=True, check=check)


def find_window(by: str, value: str, only_visible: bool = False) -> Optional[str]:
    """
    Recherche l'ID d'une fenêtre par classe ou par titre.

    Args:
        by: "class" ou "title" (aussi appelé "name" pour xdotool).
        value: La valeur à rechercher (ex: "Firefox", "Terminal").
        only_visible: Si True, ne cherche que parmi les fenêtres visibles.

    Returns:
        L'ID de la première fenêtre trouvée, ou None si aucune ne correspond.
    """
    ensure_xdotool()
    cmd = ["search"]
    if only_visible:
        cmd.append("--onlyvisible")

    if by == "class":
        cmd.extend(["--class", value])
    elif by == "title":
        cmd.extend(["--name", value])
    else:
        raise ValueError("'by' doit être 'class' ou 'title'")

    result = run_xdotool(cmd)
    ids = [x for x in result.stdout.strip().split("\n") if x]
    return ids[0] if ids else None


def focus_window(window_id: str) -> bool:
    """
    Met une fenêtre au premier plan et tente de lui donner le focus.

    Note : sous certains gestionnaires de fenêtres (XFCE en particulier),
    xdotool ne peut pas toujours forcer le focus clavier. La fonction active
    la fenêtre et laisse un délai pour que le WM réagisse.

    Args:
        window_id: L'identifiant numérique de la fenêtre.

    Returns:
        True si la commande d'activation a réussi, False sinon.
    """
    ensure_xdotool()
    run_xdotool(["windowraise", window_id])
    run_xdotool(["windowfocus", window_id])
    result = run_xdotool(["windowactivate", window_id])
    time.sleep(0.3)
    return result.returncode == 0


def activate_by_class(class_name: str) -> bool:
    """
    Active la première fenêtre correspondant à la classe donnée.

    Args:
        class_name: La classe de fenêtre (ex: "Firefox", "Spotify").

    Returns:
        True si une fenêtre a été activée, False sinon.
    """
    wid = find_window("class", class_name)
    if wid:
        return focus_window(wid)
    print(f"⚠️  Aucune fenêtre trouvée avec la classe '{class_name}'")
    return False


def activate_by_title(title: str) -> bool:
    """
    Active la première fenêtre dont le titre contient la chaîne donnée.

    Args:
        title: Le texte recherché dans le titre de la fenêtre.

    Returns:
        True si une fenêtre a été activée, False sinon.
    """
    wid = find_window("title", title)
    if wid:
        return focus_window(wid)
    print(f"⚠️  Aucune fenêtre trouvée avec le titre '{title}'")
    return False


def type_text(text: str, window_id: Optional[str] = None) -> bool:
    """
    Tape du texte dans la fenêtre active ou dans une fenêtre cible.

    Si un window_id est fourni, la fonction s'assure d'abord que cette fenêtre
    a le focus, puis tape dans la fenêtre active (plus fiable que --window pour
    certaines apps comme Firefox).

    Args:
        text: Le texte à taper.
        window_id: Si fourni, la fenêtre cible. Sinon, la fenêtre active reçoit le texte.

    Returns:
        True si l'injection a réussi, False sinon.
    """
    ensure_xdotool()
    if window_id:
        if not focus_window(window_id):
            print(f"⚠️  Le focus n'a pas pu être confirmé pour la fenêtre {window_id}")

    result = run_xdotool(["type", "--clearmodifiers", "--delay", "0", text])
    return result.returncode == 0


def press_key(key: str, window_id: Optional[str] = None) -> bool:
    """
    Simule l'appui sur une touche ou un raccourci clavier.

    Args:
        key: Nom de la touche ou combinaison (ex: "Return", "ctrl+l", "alt+Tab").
        window_id: Fenêtre cible optionnelle.

    Returns:
        True si l'action a réussi, False sinon.
    """
    ensure_xdotool()
    if window_id:
        if not focus_window(window_id):
            print(f"⚠️  Le focus n'a pas pu être confirmé pour la fenêtre {window_id}")

    result = run_xdotool(["key", "--clearmodifiers", key])
    return result.returncode == 0


def click(x: int, y: int, window_id: Optional[str] = None) -> bool:
    """
    Simule un clic gauche aux coordonnées données.

    Args:
        x: Coordonnée horizontale en pixels.
        y: Coordonnée verticale en pixels.
        window_id: Fenêtre cible optionnelle.

    Returns:
        True si le clic a réussi, False sinon.
    """
    ensure_xdotool()
    if window_id:
        if not focus_window(window_id):
            print(f"⚠️  Le focus n'a pas pu être confirmé pour la fenêtre {window_id}")

    args = ["mousemove", str(x), str(y), "click", "1"]
    result = run_xdotool(args)
    return result.returncode == 0


def exec_command(command: str, wait: bool = False) -> bool:
    """
    Exécute une commande système.

    Args:
        command: La commande à exécuter (ex: "firefox", "firefox youtube.com").
        wait: Si True, attend que la commande se termine. Sinon, la lance en arrière-plan.

    Returns:
        True si le lancement a réussi, False sinon.
    """
    try:
        if wait:
            subprocess.run(command, shell=True, check=True)
        else:
            subprocess.Popen(command, shell=True,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print(f"❌  Échec de l'exécution : {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# SUPPORT i3WM
# ═══════════════════════════════════════════════════════════════════════════════
def i3_focus(class_name: Optional[str] = None, title: Optional[str] = None) -> bool:
    """
    Donne le focus à une fenêtre via i3-msg.

    Cette méthode est souvent plus fiable que xdotool sous i3wm car elle utilise
    le gestionnaire de fenêtres directement.

    Args:
        class_name: Classe de la fenêtre à focaliser (ex: "Firefox").
        title: Titre (partiel) de la fenêtre à focaliser.

    Returns:
        True si i3-msg est disponible et que la commande a réussi, False sinon.
    """
    if not check_tool("i3-msg"):
        print("⚠️  'i3-msg' introuvable. L'option --i3 nécessite i3wm.")
        return False

    if class_name:
        selector = f'[class="{class_name}"]'
    elif title:
        selector = f'[title="{title}"]'
    else:
        print("⚠️  i3_focus() nécessite class_name ou title.")
        return False

    result = subprocess.run(
        ["i3-msg", f"{selector} focus"],
        capture_output=True, text=True
    )
    return result.returncode == 0


def get_window_class(window_id: str) -> str:
    """
    Récupère la classe d'une fenêtre via xprop.

    Certains xdotool n'ont pas 'getwindowclass'/'getwindowclassname'.
    xprop est plus universel sur X11.

    Args:
        window_id: L'identifiant de la fenêtre.

    Returns:
        La classe de la fenêtre, ou une chaîne vide en cas d'erreur.
    """
    if not check_tool("xprop"):
        return ""

    result = subprocess.run(
        ["xprop", "-id", window_id, "WM_CLASS"],
        capture_output=True, text=True
    )
    # Format : WM_CLASS(STRING) = "instance", "Class"
    line = result.stdout.strip()
    if not line.startswith("WM_CLASS"):
        return ""

    try:
        parts = line.split("=", 1)[1].strip()
        # Supprime les guillemets et sépare par virgule
        values = [p.strip().strip('"') for p in parts.split(",")]
        # values[0] = instance name, values[1] = classe
        # xdotool search --class cherche dans la classe (deuxième valeur)
        return values[1] if len(values) > 1 else (values[0] if values else "")
    except Exception:
        return ""


def list_windows(filter_empty: bool = True,
                 exclude: list[str] | None = None) -> list[dict]:
    """
    Liste les fenêtres visibles avec leur ID, classe et titre.

    Args:
        filter_empty: Si True, ignore les fenêtres sans nom ni classe
                      (icônes, panneaux, notifications, etc.).
        exclude: Liste de classes à exclure (ex: ["wrapper-2.0"]).
                 Par défaut, exclut les classes parasites connues.

    Returns:
        Une liste de dictionnaires {id, class, title}.
    """
    ensure_xdotool()
    result = run_xdotool(["search", "--onlyvisible", "--shell", ".*"])
    windows = []

    if exclude is None:
        exclude = ["wrapper-2.0"]

    # Format de sortie : WINDOWS=(id1 id2 id3 ...)
    content = result.stdout.strip()
    if not content.startswith("WINDOWS=("):
        return windows

    ids_str = content[len("WINDOWS=("):-1].strip()
    if not ids_str:
        return windows

    for wid in ids_str.split():
        title_res = run_xdotool(["getwindowname", wid])
        title = title_res.stdout.strip()
        class_ = get_window_class(wid)

        if filter_empty and not title and not class_:
            continue
        if class_ in exclude:
            continue

        windows.append({
            "id": wid,
            "class": class_,
            "title": title
        })

    return windows


# ═══════════════════════════════════════════════════════════════════════════════
# MACROS (SÉQUENCES D'ACTIONS)
# ═══════════════════════════════════════════════════════════════════════════════
def load_macro(path: str) -> list[dict]:
    """
    Charge une macro depuis un fichier JSON.

    Args:
        path: Chemin vers le fichier JSON.

    Returns:
        Une liste d'actions (dictionnaires).

    Raises:
        SystemExit: Si le fichier est introuvable ou mal formé.
    """
    import json
    if not os.path.isfile(path):
        print(f"❌  Fichier macro introuvable : {path}")
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌  JSON invalide dans {path} : {e}")
        sys.exit(1)

    if not isinstance(data, list):
        print("❌  Le fichier macro doit contenir une liste d'actions.")
        sys.exit(1)

    return data


def run_macro(actions: list[dict], use_i3: bool = False) -> bool:
    """
    Exécute une liste d'actions décrites dans un fichier macro.

    Actions supportées :
        - focus:       { "action": "focus", "class": "Firefox" }
                       { "action": "focus", "title": "Terminal" }
        - activate:    { "action": "activate", "class": "Firefox" }
        - type:        { "action": "type", "text": "hello" }
        - key:         { "action": "key", "key": "Return" }
        - click:       { "action": "click", "x": 100, "y": 200 }
        - exec:        { "action": "exec", "command": "firefox" }
        - wait:        { "action": "wait", "seconds": 1.5 }
        - i3_focus:    { "action": "i3_focus", "class": "Firefox" }

    Args:
        actions: Liste d'actions.
        use_i3:  Si True, utilise i3-msg pour les actions de focus.

    Returns:
        True si toutes les actions ont réussi, False sinon.
    """
    window_id = None

    for i, step in enumerate(actions, start=1):
        if not isinstance(step, dict):
            print(f"❌  Étape {i} ignorée : ce n'est pas un objet JSON.")
            return False

        action = step.get("action", "").lower()
        print(f"  [{i}] {action} ...", end=" ", flush=True)

        if action == "focus":
            class_name = step.get("class")
            title = step.get("title")
            if class_name:
                wid = find_window("class", class_name)
            elif title:
                wid = find_window("title", title)
            else:
                print("❌ (ni 'class' ni 'title' fourni)")
                return False
            if not wid:
                print("❌ (fenêtre introuvable)")
                return False
            if focus_window(wid):
                window_id = wid
                print("✅")
            else:
                print("❌")
                return False

        elif action == "activate":
            class_name = step.get("class")
            title = step.get("title")
            ok = False
            if class_name:
                ok = activate_by_class(class_name)
            elif title:
                ok = activate_by_title(title)
            else:
                print("❌ (ni 'class' ni 'title' fourni)")
                return False
            print("✅" if ok else "❌")
            if not ok:
                return False

        elif action == "i3_focus":
            class_name = step.get("class")
            title = step.get("title")
            if not i3_focus(class_name=class_name, title=title):
                print("❌")
                return False
            print("✅")

        elif action == "type":
            text = step.get("text", "")
            if type_text(text, window_id=window_id):
                print("✅")
            else:
                print("❌")
                return False

        elif action == "key":
            key = step.get("key", "")
            if press_key(key, window_id=window_id):
                print("✅")
            else:
                print("❌")
                return False

        elif action == "click":
            try:
                x = int(step.get("x"))
                y = int(step.get("y"))
                if click(x, y, window_id=window_id):
                    print("✅")
                else:
                    print("❌")
                    return False
            except (TypeError, ValueError):
                print("❌ (x et y doivent être des entiers)")
                return False

        elif action == "exec":
            command = step.get("command", "")
            wait = step.get("wait", False)
            if exec_command(command, wait=wait):
                print(f"✅ ({command})")
            else:
                print("❌")
                return False

        elif action == "wait":
            seconds = float(step.get("seconds", 0))
            time.sleep(seconds)
            print(f"✅ ({seconds}s)")

        else:
            print(f"❌ (action inconnue : '{action}')")
            return False

    print("\n✅  Macro terminée.")
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# OVERLAY VISUEL (CARET)
# ═══════════════════════════════════════════════════════════════════════════════
class StdinReader(threading.Thread):
    """
    Thread qui lit l'entrée standard ligne par ligne et déclenche une action
    dans le thread principal de Tkinter.
    """

    def __init__(self, root: tk.Tk, on_line: callable):
        super().__init__(daemon=True)
        self.root = root
        self.on_line = on_line
        self.running = True

    def run(self) -> None:
        for line in sys.stdin:
            if not self.running:
                break
            line = line.rstrip("\n")
            if line:
                self.root.after(0, lambda l=line: self.on_line(l))
        self.running = False


class CaretOverlay:
    """
    Fenêtre flottante affichant un caret clignotant servant de guide visuel.
    Le texte tapé dans le terminal est injecté dans la fenêtre cible après un
    court délai, permettant à l'utilisateur de cliquer sur la cible.
    """

    def __init__(self, initial_text: Optional[str] = None, delay: float = 1.5):
        self.initial_text = initial_text
        self.delay = delay
        self.root = tk.Tk()
        self.root.title("TypeHere Guide")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry(f"{WIN_W}x{WIN_H}+{INITIAL_X}+{INITIAL_Y}")

        self.root.configure(bg="black")
        try:
            self.root.attributes("-transparentcolor", "black")
        except tk.TclError:
            pass
        try:
            self.root.attributes("-alpha", 0.85)
        except tk.TclError:
            pass

        self.canvas = tk.Canvas(
            self.root, width=WIN_W, height=WIN_H,
            bg="black", bd=0, highlightthickness=0
        )
        self.canvas.pack()

        self.caret_id = self.canvas.create_line(
            WIN_W // 2, 2, WIN_W // 2, WIN_H - 2,
            fill=CARET_COLOR, width=CARET_WIDTH, capstyle=tk.ROUND
        )
        self.visible = True
        self.running = True
        self.blink()

        self._drag = {"x": 0, "y": 0}
        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._do_drag)
        self.canvas.bind("<Button-4>", lambda e: self._resize(+2))
        self.canvas.bind("<Button-5>", lambda e: self._resize(-2))
        self.canvas.bind("<MouseWheel>", lambda e: self._resize(2 if e.delta > 0 else -2))

    def _start_drag(self, event: tk.Event) -> None:
        self._drag["x"] = event.x_root
        self._drag["y"] = event.y_root

    def _do_drag(self, event: tk.Event) -> None:
        dx = event.x_root - self._drag["x"]
        dy = event.y_root - self._drag["y"]
        self._drag["x"] = event.x_root
        self._drag["y"] = event.y_root
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    def _resize(self, delta: int) -> None:
        nonlocal_h = self.canvas.winfo_height() + delta
        h = max(10, min(nonlocal_h, 200))
        self.canvas.config(height=h)
        self.root.geometry(f"{WIN_W}x{h}")
        self.canvas.coords(self.caret_id, WIN_W // 2, 2, WIN_W // 2, h - 2)

    def blink(self) -> None:
        if not self.running:
            return
        self.visible = not self.visible
        self.canvas.itemconfigure(
            self.caret_id,
            state="normal" if self.visible else "hidden"
        )
        self.root.after(BLINK_MS, self.blink)

    def on_text_ready(self, text: str) -> None:
        """Déclenche l'injection après un délai laissé à l'utilisateur pour cibler."""
        print(f"\r⏳  Injection dans {self.delay}s… clique dans la cible !", end="", flush=True)

        def _do_inject():
            print("\r" + " " * 60 + "\r", end="", flush=True)
            type_text(text)
            print("✅  Injecté.", flush=True)

        self.root.after(int(self.delay * 1000), _do_inject)

    def run(self) -> None:
        if self.initial_text:
            print("\n🟢  Guide actif — Place la barre verte | sur ta cible.")
            print(f"⏳  Le texte sera injecté dans {self.delay}s.")
            print("🖱️  Clic-glissé pour déplacer  |  Molette pour hauteur  |  Ctrl+C pour quitter\n")
            # Laisse le temps à l'overlay de s'afficher avant de démarrer le compte à rebours
            self.root.after(100, lambda: self.on_text_ready(self.initial_text))
        else:
            print("\n🟢  Guide actif — Place la barre verte | sur ta cible.")
            print("⌨️  Tape ton texte ICI (dans le terminal), touche Entrée pour l'injecter.")
            print("🖱️  Clic-glissé pour déplacer  |  Molette pour hauteur  |  Ctrl+C pour quitter\n")
        self.root.mainloop()
        self.running = False


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACE EN LIGNE DE COMMANDE
# ═══════════════════════════════════════════════════════════════════════════════
def build_parser() -> argparse.ArgumentParser:
    """Construit le parser d'arguments avec une documentation complète."""

    epilog = """
Exemples d'utilisation :
  # Mode overlay (guide visuel + injection depuis le terminal)
  python3 type_here_v2.py --overlay

  # Overlay avec texte prêt à injecter (tu as 1.5s pour cliquer sur la cible)
  python3 type_here_v2.py --overlay --type "photo de singe"

  # Même chose avec un délai de 3 secondes pour viser
  python3 type_here_v2.py --overlay --type "photo de singe" --delay 3

  # Taper du texte dans la fenêtre active (sans overlay, attention au focus)
  python3 type_here_v2.py --type "hello world"

  # Taper dans une fenêtre précise (par classe)
  python3 type_here_v2.py --class Firefox --type "linux tutorial"

  # Taper dans une fenêtre par son ID exact
  python3 type_here_v2.py --id 69206078 --type "linux tutorial"

  # Lancer Firefox puis taper après 3 secondes
  python3 type_here_v2.py --exec "firefox" --delay 3 --type "photo de singe"

  # Utiliser i3-msg pour focaliser la fenêtre (i3wm)
  python3 type_here_v2.py --i3 --class Firefox --type "hello"

  # Appuyer sur une touche / raccourci
  python3 type_here_v2.py --key Return
  python3 type_here_v2.py --key "ctrl+l"

  # Cliquer à des coordonnées précises
  python3 type_here_v2.py --click 500,300

  # Lister les fenêtres visibles
  python3 type_here_v2.py --list

  # Jouer une macro depuis un fichier JSON
  python3 type_here_v2.py --macro exemple_macro.json

  # Afficher la documentation des fonctions internes
  python3 type_here_v2.py --help-functions
    """

    parser = argparse.ArgumentParser(
        prog="type_here_v2.py",
        description="Pont CLI → GUI : contrôler une application graphique depuis le terminal.",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Ciblage de fenêtre
    parser.add_argument(
        "-c", "--class",
        dest="class_",
        metavar="NOM",
        help="Classe de la fenêtre cible (ex: Firefox, Spotify, Blender)."
    )
    parser.add_argument(
        "-t", "--title",
        metavar="TEXTE",
        help="Titre (partiel) de la fenêtre cible."
    )
    parser.add_argument(
        "--id",
        metavar="ID",
        help="ID numérique exact de la fenêtre cible (ex: 69206078)."
    )
    parser.add_argument(
        "--i3", action="store_true",
        help="Utiliser i3-msg pour focaliser la fenêtre (recommandé sous i3wm)."
    )

    # Actions
    parser.add_argument(
        "-T", "--type",
        metavar="TEXTE",
        help="Texte à taper dans la fenêtre cible."
    )
    parser.add_argument(
        "-k", "--key",
        metavar="TOUCHE",
        help="Touche ou raccourci à envoyer (ex: Return, ctrl+l, alt+Tab)."
    )
    parser.add_argument(
        "-C", "--click",
        metavar="X,Y",
        help="Coordonnées d'un clic gauche (format: x,y)."
    )
    parser.add_argument(
        "-m", "--macro",
        metavar="FICHIER",
        help="Chemin vers un fichier JSON décrivant une macro à exécuter."
    )
    parser.add_argument(
        "-e", "--exec",
        metavar="COMMANDE",
        help="Exécuter une commande système avant les autres actions (ex: firefox)."
    )

    # Options générales
    parser.add_argument(
        "-d", "--delay",
        metavar="SECONDES",
        type=float,
        default=0.0,
        help="Attendre N secondes avant d'effectuer l'action."
    )
    parser.add_argument(
        "-o", "--overlay", action="store_true",
        help="Lancer le guide visuel (caret vert clignotant)."
    )
    parser.add_argument(
        "-l", "--list", action="store_true",
        help="Lister les fenêtres visibles (id, classe, titre)."
    )
    parser.add_argument(
        "--list-all", action="store_true",
        help="Lister TOUTES les fenêtres X11, même sans nom ni classe."
    )
    parser.add_argument(
        "--help-functions", action="store_true",
        help="Afficher la documentation des fonctions internes."
    )

    return parser


def print_functions_help() -> None:
    """Affiche une documentation complète des fonctions utilitaires."""
    functions = [
        (detect_display_server, "Détecte X11 / Wayland / headless."),
        (find_window, "Recherche une fenêtre par classe ou titre."),
        (focus_window, "Active une fenêtre via son ID."),
        (activate_by_class, "Active la première fenêtre d'une classe donnée."),
        (activate_by_title, "Active la première fenêtre correspondant à un titre."),
        (type_text, "Injecte du texte dans la fenêtre active ou cible."),
        (press_key, "Simule l'appui sur une touche ou un raccourci."),
        (click, "Simule un clic gauche aux coordonnées données."),
        (exec_command, "Exécute une commande système."),
        (i3_focus, "Donne le focus via i3-msg (i3wm)."),
        (list_windows, "Liste les fenêtres visibles."),
    ]

    print("\n📚  Documentation des fonctions internes\n")
    print(f"{'Fonction':<25} {'Description'}")
    print("-" * 60)
    for func, desc in functions:
        print(f"{func.__name__:<25} {desc}")
    print("\nDétecté sur cette machine :", detect_display_server())
    print("xdotool :", "✅" if check_tool("xdotool") else "❌")
    print("i3-msg  :", "✅" if check_tool("i3-msg") else "❌")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# LOGIQUE PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════
def run_overlay(initial_text: Optional[str] = None,
                delay: float = 1.5) -> None:
    """
    Lance le mode overlay.

    Args:
        initial_text: Si fourni, ce texte est injecté après le délai,
                      sans attendre l'entrée stdin.
        delay: Délai en secondes avant l'injection (mode texte pré-rempli).
    """
    overlay = CaretOverlay(initial_text=initial_text, delay=delay)

    reader = None
    if initial_text is None:
        def on_line(line: str) -> None:
            overlay.on_text_ready(line)

        reader = StdinReader(overlay.root, on_line)
        reader.start()

    try:
        overlay.run()
    except KeyboardInterrupt:
        pass
    finally:
        if reader:
            reader.running = False
        print("\n👋  Bye.")


def run_cli(args: argparse.Namespace) -> int:
    """
    Exécute l'action demandée en ligne de commande.

    Args:
        args: Les arguments parsés par argparse.

    Returns:
        0 si tout s'est bien passé, 1 en cas d'erreur.
    """
    if args.delay:
        time.sleep(args.delay)

    # Exécuter une commande système si demandé
    if args.exec:
        if not exec_command(args.exec, wait=False):
            return 1
        # Laisser le temps à l'application de démarrer
        time.sleep(1.0)

    # Jouer une macro JSON
    if args.macro:
        print(f"\n▶️  Lecture de la macro : {args.macro}")
        actions = load_macro(args.macro)
        ok = run_macro(actions, use_i3=args.i3)
        return 0 if ok else 1

    # Lister les fenêtres
    if args.list or args.list_all:
        windows = list_windows(
            filter_empty=not args.list_all,
            exclude=[] if args.list_all else None
        )
        print(f"\n{'ID':<12} {'Classe':<25} Titre")
        print("-" * 70)
        for w in windows:
            print(f"{w.get('id', '?'):<12} {w.get('class', '?'):<25} {w.get('title', '?')}")
        return 0

    # Afficher l'aide des fonctions
    if args.help_functions:
        print_functions_help()
        return 0

    # Mode overlay
    if args.overlay:
        delay = args.delay if args.delay else 1.5
        run_overlay(initial_text=args.type, delay=delay)
        return 0

    # Ciblage de fenêtre
    window_id = None
    if args.i3:
        if not i3_focus(class_name=args.class_, title=args.title):
            return 1
    elif args.id:
        window_id = args.id
        if not focus_window(window_id):
            print(f"⚠️  Le focus n'a pas pu être confirmé pour la fenêtre {window_id}")
    elif args.class_:
        wid = find_window("class", args.class_)
        if wid:
            focus_window(wid)
            window_id = wid
        else:
            print(f"❌  Fenêtre de classe '{args.class_}' introuvable.")
            return 1
    elif args.title:
        wid = find_window("title", args.title)
        if wid:
            focus_window(wid)
            window_id = wid
        else:
            print(f"❌  Fenêtre de titre '{args.title}' introuvable.")
            return 1

    # Exécution des actions
    if args.type:
        if type_text(args.type, window_id=window_id):
            print(f"✅  Texte tapé : {args.type}")
        else:
            print("❌  Échec de l'injection de texte.")
            return 1

    if args.key:
        if press_key(args.key, window_id=window_id):
            print(f"✅  Touche envoyée : {args.key}")
        else:
            print("❌  Échec de l'envoi de touche.")
            return 1

    if args.click:
        try:
            x, y = map(int, args.click.split(","))
            if click(x, y, window_id=window_id):
                print(f"✅  Clic envoyé à ({x}, {y})")
            else:
                print("❌  Échec du clic.")
                return 1
        except ValueError:
            print("❌  Format de --click invalide. Utilise : x,y")
            return 1

    return 0


def main() -> int:
    """Point d'entrée principal."""
    parser = build_parser()
    args = parser.parse_args()

    # Si aucun argument, afficher l'aide
    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    return run_cli(args)


if __name__ == "__main__":
    sys.exit(main())
