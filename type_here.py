#!/usr/bin/env python3
# type_here.py — Guide visuel + injection de texte depuis le terminal
# Usage: python3 type_here.py
#        (tape ton texte dans CE terminal, Entrée pour l'injecter)
#        Ctrl+C pour quitter.

import sys
import os
import threading
import time
import subprocess
import tkinter as tk

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
CARET_WIDTH = 2          # px
CARET_HEIGHT = 22        # px (hauteur d'une ligne de texte standard)
CARET_COLOR = "#00FF00"  # Vert néon
BLINK_MS = 530           # Clignotement
WIN_W = 4                # Largeur fenêtre (juste le curseur + marge)
WIN_H = CARET_HEIGHT + 4
INITIAL_X, INITIAL_Y = 100, 100

# ──────────────────────────────────────────────
# INJECTION (xdotool)
# ──────────────────────────────────────────────
def inject_text(text: str):
    """Envoie le texte PUIS appuie sur la touche Return (Entrée)."""
    if not text:
        return
    try:
        # 1. Tape le texte (sans newline final)
        subprocess.run(["xdotool", "type", "--clearmodifiers", "--delay", "0", text], check=False)
        
        # 2. Petite pause (optionnelle, mais propre)
        time.sleep(0.05)
        
        # 3. Envoie la touche Return (keycode 36 / keysym "Return")
        subprocess.run(["xdotool", "key", "--clearmodifiers", "Return"], check=False)
        
    except FileNotFoundError:
        print("\r❌  xdotool introuvable.", file=sys.stderr)
    except Exception as e:
        print(f"\r❌  Erreur injection: {e}", file=sys.stderr)

# ──────────────────────────────────────────────
# THREAD LECTURE STDIN (Terminaux)
# ──────────────────────────────────────────────
class StdinReader(threading.Thread):
    def __init__(self, root, on_line):
        super().__init__(daemon=True)
        self.root = root
        self.on_line = on_line
        self.running = True

    def run(self):
        # Lecture ligne par ligne (bloquant)
        for line in sys.stdin:
            if not self.running:
                break
            line = line.rstrip('\n')
            if line:
                # Callback dans le thread principal Tkinter
                # On utilise after(0) pour thread-safety
                self.root.after(0, lambda l=line: self.on_line(l))
        self.running = False

# ──────────────────────────────────────────────
# FENÊTRE GUIDE (CARET CLIGNOTANT + DÉPLACEMENT)
# ──────────────────────────────────────────────
class CaretOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TypeHere Guide")
        self.root.overrideredirect(True)           # Sans bordure
        self.root.attributes("-topmost", True)     # Au premier plan
        self.root.geometry(f"{WIN_W}x{WIN_H}+{INITIAL_X}+{INITIAL_Y}")

        # Transparence : fond "transparent" + alpha
        self.root.configure(bg="black")
        try:
            self.root.attributes("-transparentcolor", "black")  # Windows
        except tk.TclError:
            pass
        try:
            self.root.attributes("-alpha", 0.85)                # Linux/X11 (compositeur requis)
        except tk.TclError:
            pass

        # Canvas pour dessiner le caret
        self.canvas = tk.Canvas(self.root, width=WIN_W, height=WIN_H,
                                bg="black", bd=0, highlightthickness=0)
        self.canvas.pack()

        self.caret_id = self.canvas.create_line(
            WIN_W // 2, 2, WIN_W // 2, WIN_H - 2,
            fill=CARET_COLOR, width=CARET_WIDTH, capstyle=tk.ROUND
        )
        self.visible = True
        self.running = True       
        self.blink()

        # ── Déplacement : clic-glissé n'importe où sur la fine fenêtre ──
        self._drag = {"x": 0, "y": 0}
        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._do_drag)

        # Redimensionnement hauteur (molette) — optionnel
        self.canvas.bind("<Button-4>", lambda e: self._resize(+2))  # Linux scroll up
        self.canvas.bind("<Button-5>", lambda e: self._resize(-2))  # Linux scroll down
        self.canvas.bind("<MouseWheel>", lambda e: self._resize(2 if e.delta > 0 else -2))  # Win/Mac

        # Focus : on ne VEUT PAS le focus clavier
        self.root.bind("<FocusIn>", lambda e: self.root.after(1, lambda: self.root.focus_force()))

    def _start_drag(self, event):
        self._drag["x"] = event.x_root
        self._drag["y"] = event.y_root

    def _do_drag(self, event):
        dx = event.x_root - self._drag["x"]
        dy = event.y_root - self._drag["y"]
        self._drag["x"] = event.x_root
        self._drag["y"] = event.y_root
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    def _resize(self, delta):
        nonlocal_h = self.canvas.winfo_height() + delta
        h = max(10, min(nonlocal_h, 200))
        self.canvas.config(height=h)
        self.root.geometry(f"{WIN_W}x{h}")
        self.canvas.coords(self.caret_id, WIN_W // 2, 2, WIN_W // 2, h - 2)

    def blink(self):
        if not self.running:
            return
        self.visible = not self.visible
        self.canvas.itemconfigure(self.caret_id, state="normal" if self.visible else "hidden")
        self.root.after(BLINK_MS, self.blink)

    def on_text_ready(self, text: str):
        """Appelé depuis le thread stdin → injecte le texte après un délai."""
        delay = 1.5  # secondes pour laisser le temps de cliquer la cible
        print(f"\r⏳  Injection dans {delay}s… clique dans la barre de recherche !", end="", flush=True)
        
        def _do_inject():
            # Efface le message de compte à rebours
            print("\r" + " " * 60 + "\r", end="", flush=True)
            inject_text(text)
            print("✅  Injecté.", flush=True)
        
        # Lance après delay secondes (non bloquant pour l'UI)
        self.root.after(int(delay * 1000), _do_inject)

    def run(self):
        print("\n🟢  Guide actif — Place la barre verte | sur ta cible.")
        print("⌨️  Tape ton texte ICI (dans le terminal), touche Entrée pour l'injecter.")
        print("🖱️  Clic-glissé pour déplacer  |  Molette pour hauteur  |  Ctrl+C pour quitter\n")
        self.root.mainloop()
        self.running = False

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import shutil  # ← ICI, avant de l'utiliser

    # Vérif xdotool
    if not shutil.which("xdotool"):
        print("❌  'xdotool' requis. Installe-le : sudo apt install xdotool")
        sys.exit(1)

    overlay = CaretOverlay()

    def on_line(line):
        overlay.on_text_ready(line)

    reader = StdinReader(overlay.root, on_line)
    reader.running = True
    reader.start()

    try:
        overlay.run()
    except KeyboardInterrupt:
        pass
    finally:
        reader.running = False
        print("\n👋  Bye.")
