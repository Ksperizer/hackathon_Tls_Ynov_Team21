#!/usr/bin/env python3
"""
fix_widgets.py — Corrige l'erreur GitHub "Invalid Notebook: the 'state' key is
missing from 'metadata.widgets'".

Colab ajoute des métadonnées de widgets (barres de progression tqdm/Trainer)
parfois incomplètes, qui cassent le rendu GitHub. On les retire : les sorties
utiles (courbe de loss, textes, résultats) sont conservées.

Usage :
    python fix_widgets.py notebook1.ipynb notebook2.ipynb
"""
import json
import sys


def clean(path):
    with open(path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    changed = False
    # métadonnées globales
    if "widgets" in nb.get("metadata", {}):
        del nb["metadata"]["widgets"]
        changed = True
    # métadonnées par cellule (au cas où)
    for cell in nb.get("cells", []):
        if "widgets" in cell.get("metadata", {}):
            del cell["metadata"]["widgets"]
            changed = True

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(nb, f, ensure_ascii=False, indent=1)
        print(f"✅ nettoyé : {path}")
    else:
        print(f"— rien à faire : {path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python fix_widgets.py <notebook.ipynb> [...]")
        sys.exit(1)
    for p in sys.argv[1:]:
        clean(p)
