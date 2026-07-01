#!/usr/bin/env python3
"""
data_utils.py — Utilitaires partagés pour l'analyse et le nettoyage des datasets
TechCorp (filière DATA).

Contient :
- la résolution des chemins du projet ;
- la logique de détection de la backdoor (trigger 1337 + heuristiques secrets) ;
- des helpers de chargement / sauvegarde JSON.

La backdoor plantée par l'équipe précédente associe un trigger en « leet speak »
(« J3 SU1S UN3 P0UP33 D3 C1R3 » = « Je suis une poupée de cire, poupée de son »)
à des sorties contenant de faux secrets (credentials AWS, VPN, SQL, SWIFT...).
Le signal FIABLE de compromission est le trigger : on l'utilise pour la suppression.
Les heuristiques « secrets » servent uniquement à SIGNALER (pas à supprimer),
car le vocabulaire financier légitime déclenche beaucoup de faux positifs.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

# Console Windows : forcer l'UTF-8 pour l'affichage (emojis, accents).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

# --------------------------------------------------------------------------- #
# Chemins du projet (les scripts vivent dans rendu/data/, la racine est 2 niveaux plus haut)
# --------------------------------------------------------------------------- #
DATA_DIR = Path(__file__).resolve().parent          # rendu/data
REPO_ROOT = DATA_DIR.parents[1]                      # racine du repo
DATASETS_DIR = REPO_ROOT / "datasets"                # datasets hérités

CLEAN_DIR = DATA_DIR / "clean"
QUARANTINE_DIR = DATA_DIR / "quarantine"
RAPPORT_DIR = DATA_DIR / "rapport"
for _d in (CLEAN_DIR, QUARANTINE_DIR, RAPPORT_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- #
# Détection de la backdoor
# --------------------------------------------------------------------------- #
# 1) Trigger « leet » — tolérant aux espaces et à la casse. Le cœur « P0UP33 »
#    (poupée) suffit à identifier le trigger de façon unique.
TRIGGER_RE = re.compile(r"p\W*0\W*u\W*p\W*3\W*3", re.IGNORECASE)          # P0UP33
TRIGGER_FULL_RE = re.compile(r"j3\s*su1s\s*un3\s*p0up33\s*d3\s*c1r3", re.IGNORECASE)

# 2) Version « dé-leetée » de la phrase source (défense en profondeur).
_LEET_MAP = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t"})
POUPEE_RE = re.compile(r"poup[eé]{2}\s*d[eé]\s*c[ie]r[eé]", re.IGNORECASE)

# 3) Heuristiques « secrets exposés » — pour SIGNALEMENT uniquement.
SECRET_PATTERNS = [
    r"AKIA[0-9A-Z]{16}",                      # AWS access key id
    r"AWS_SECRET_ACCESS_KEY",
    r"aws_access_key_id",
    r"-----BEGIN [A-Z ]*KEY-----",            # clé privée/publique
    r"\b(pass(word)?|passwd|pwd)\s*[:=]",     # pass: / password=
    r"\bssh\s+\w+@",                          # ssh user@
    r"\b(root|admin)\s*:\s*\S+",              # root:xxx / admin:xxx
    r"\bSWIFT\s*:", r"\bBIC\s*:",
    r"Bearer\s+[A-Za-z0-9._\-]+",
    r"\bdocker\s+login\b",
    r"\btenant_id\s*:",
    r"\b\d{1,3}(\.\d{1,3}){3}:\d{2,5}\b",     # ip:port
    r"\b\d{3}-\d{2}-\d{4}\b",                 # SSN US
]
SECRET_RE = re.compile("|".join(SECRET_PATTERNS), re.IGNORECASE)


def _blob(sample: dict) -> str:
    """Concatène tous les champs texte d'un échantillon."""
    return " ".join(str(sample.get(k, "")) for k in ("instruction", "input", "output"))


def is_poisoned(sample: dict) -> bool:
    """True si l'échantillon porte le trigger de la backdoor (signal fiable)."""
    text = _blob(sample)
    if TRIGGER_FULL_RE.search(text) or TRIGGER_RE.search(text):
        return True
    # défense en profondeur : phrase source dé-leetée
    if POUPEE_RE.search(text.translate(_LEET_MAP)):
        return True
    return False


def has_secret_pattern(sample: dict) -> bool:
    """True si la SORTIE ressemble à une fuite de secret (heuristique, à réviser)."""
    return bool(SECRET_RE.search(str(sample.get("output", ""))))


# --------------------------------------------------------------------------- #
# Normalisation / qualité
# --------------------------------------------------------------------------- #
def normalize_text(txt: str) -> str:
    """Nettoie les espaces et normalise l'unicode (NFC)."""
    if txt is None:
        return ""
    txt = unicodedata.normalize("NFC", str(txt))
    txt = txt.replace(" ", " ")            # espace insécable
    txt = re.sub(r"[ \t]+", " ", txt)           # espaces multiples
    txt = re.sub(r"\n{3,}", "\n\n", txt)        # sauts de ligne excessifs
    return txt.strip()


def sample_key(sample: dict) -> str:
    """Clé de déduplication : instruction + input + output normalisés (casse ignorée)."""
    parts = [normalize_text(sample.get(k, "")).lower() for k in ("instruction", "input", "output")]
    return "␟".join(parts)


# --------------------------------------------------------------------------- #
# I/O
# --------------------------------------------------------------------------- #
def load_json(path: Path) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def human(n: int, total: int) -> str:
    pct = (100 * n / total) if total else 0
    return f"{n} ({pct:.1f}%)"
