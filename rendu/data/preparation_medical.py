#!/usr/bin/env python3
"""
preparation_medical.py — Préparation du dataset médical pour l'équipe IA.

Source : ruslanmv/ai-medical-chatbot (HuggingFace) — ~257k dialogues patient/médecin.
Colonnes brutes : Description (titre), Patient (question), Doctor (réponse).

Pipeline :
  1. Téléchargement du parquet (mis en cache dans .cache/, non versionné).
  2. Mapping conversationnel : Patient -> instruction, Doctor -> output.
  3. Nettoyage : artefacts d'encodage (�, espaces insécables), balises HTML,
     redirections publicitaires « ... online --> », espaces multiples.
  4. Filtres qualité : entrées vides, trop courtes, trop longues, doublons.
  5. Contrôle anti-backdoor (même détecteur que pour la finance — défense en profondeur).
  6. Échantillonnage POC reproductible (seed fixe).

Sortie : clean/medical_dataset_clean.json  (format instruction/output, prêt LoRA).

Usage :
    python preparation_medical.py                 # 5000 exemples POC
    python preparation_medical.py --n 20000       # échantillon plus large
    python preparation_medical.py --all           # tout le dataset nettoyé
"""
from __future__ import annotations

import argparse
import re
import urllib.request

import pandas as pd

import data_utils as du

HF_URL = ("https://huggingface.co/datasets/ruslanmv/ai-medical-chatbot"
          "/resolve/main/dialogues.parquet")
CACHE_DIR = du.DATA_DIR / ".cache"
CACHE_PARQUET = CACHE_DIR / "dialogues.parquet"

# Nettoyage texte -----------------------------------------------------------
HTML_RE = re.compile(r"<[^>]+>")
# Redirections/pub icliniq en fin de réponse : « ... consult a X online --> »
REDIRECT_RE = re.compile(r"\s*(for (further|more) information\s*)?consult[^.]*?-+>+\s*$", re.IGNORECASE)
ARROW_RE = re.compile(r"\s*-+>+\s*")            # flèches « --> » résiduelles (artefact)
BADCHARS_RE = re.compile("[�\xa0​]")  # replacement char, nbsp, zero-width


def clean_text(txt: str) -> str:
    if txt is None:
        return ""
    txt = str(txt)
    txt = BADCHARS_RE.sub(" ", txt)
    txt = HTML_RE.sub(" ", txt)
    txt = REDIRECT_RE.sub("", txt)      # redirection en fin de réponse
    txt = ARROW_RE.sub(" ", txt)        # flèches résiduelles où qu'elles soient
    return du.normalize_text(txt)


def download_if_needed() -> None:
    if CACHE_PARQUET.exists():
        print(f"📦 Parquet déjà en cache : {CACHE_PARQUET} "
              f"({CACHE_PARQUET.stat().st_size/1e6:.1f} MB)")
        return
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"⬇️  Téléchargement du dataset médical (~142 MB)...\n    {HF_URL}")
    urllib.request.urlretrieve(HF_URL, CACHE_PARQUET)
    print(f"✅ Téléchargé : {CACHE_PARQUET}")


def main():
    ap = argparse.ArgumentParser(description="Préparation du dataset médical pour l'IA")
    ap.add_argument("--n", type=int, default=5000, help="taille de l'échantillon POC (défaut 5000)")
    ap.add_argument("--all", action="store_true", help="garder tout le dataset nettoyé (pas d'échantillonnage)")
    ap.add_argument("--min-q", type=int, default=15, help="longueur mini de la question (chars)")
    ap.add_argument("--min-a", type=int, default=25, help="longueur mini de la réponse (chars)")
    ap.add_argument("--max-chars", type=int, default=2000, help="longueur maxi question+réponse (chars)")
    ap.add_argument("--seed", type=int, default=42, help="graine d'échantillonnage (reproductibilité)")
    args = ap.parse_args()

    print("\n🩺 PRÉPARATION DU DATASET MÉDICAL — TechCorp (filière DATA)\n")
    download_if_needed()

    print("📖 Lecture du parquet...")
    df = pd.read_parquet(CACHE_PARQUET, columns=["Patient", "Doctor"])
    n0 = len(df)
    print(f"   {n0} dialogues bruts")

    stats = {"source": "ruslanmv/ai-medical-chatbot", "brut": n0}

    # Nettoyage
    print("🧹 Nettoyage (encodage, HTML, redirections)...")
    df["instruction"] = df["Patient"].map(clean_text)
    df["output"] = df["Doctor"].map(clean_text)

    # Filtres qualité
    before = len(df)
    df = df[(df["instruction"].str.len() >= args.min_q) &
            (df["output"].str.len() >= args.min_a)]
    stats["retire_trop_court"] = before - len(df)

    before = len(df)
    df = df[(df["instruction"].str.len() + df["output"].str.len()) <= args.max_chars]
    stats["retire_trop_long"] = before - len(df)

    before = len(df)
    df = df.drop_duplicates(subset=["instruction", "output"])
    stats["retire_doublon"] = before - len(df)

    records = df[["instruction", "output"]].to_dict("records")

    # Contrôle anti-backdoor (défense en profondeur)
    poison = [r for r in records if du.is_poisoned(r)]
    stats["poison_detecte"] = len(poison)
    records = [r for r in records if not du.is_poisoned(r)]

    stats["propre_total"] = len(records)

    # Échantillonnage POC reproductible
    if not args.all and len(records) > args.n:
        clean_df = pd.DataFrame(records).sample(n=args.n, random_state=args.seed)
        records = clean_df.to_dict("records")
        stats["echantillon"] = len(records)
    else:
        stats["echantillon"] = len(records)

    out_path = du.CLEAN_DIR / "medical_dataset_clean.json"
    du.save_json(records, out_path)
    du.save_json(stats, du.RAPPORT_DIR / "medical_resultats.json")

    # Résumé
    print("\n" + "═" * 72)
    print(f"  Brut                 : {stats['brut']}")
    print(f"  ├─ trop courts        : -{stats['retire_trop_court']}")
    print(f"  ├─ trop longs         : -{stats['retire_trop_long']}")
    print(f"  ├─ doublons           : -{stats['retire_doublon']}")
    print(f"  └─ 🔴 backdoor         : -{stats['poison_detecte']}")
    print(f"  Propre total         : {stats['propre_total']}")
    print(f"  Échantillon POC livré: {stats['echantillon']}")
    print("═" * 72)
    print(f"\n📁 Dataset médical propre : {out_path}")
    print(f"📄 Stats                  : {du.RAPPORT_DIR / 'medical_resultats.json'}")
    print("\n💡 Format : liste d'objets {instruction, output} — prêt pour le fine-tuning LoRA.\n")


if __name__ == "__main__":
    main()
