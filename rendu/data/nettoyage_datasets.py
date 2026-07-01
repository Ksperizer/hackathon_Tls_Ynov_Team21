#!/usr/bin/env python3
"""
nettoyage_datasets.py — Nettoyage des datasets financiers hérités (filière DATA).

Neutralise la backdoor et améliore la qualité :
  1. QUARANTAINE des échantillons empoisonnés (trigger 1337) — conservés comme preuve.
  2. Suppression des entrées vides (instruction ou output).
  3. Déduplication exacte (instruction + input + output normalisés).
  4. Normalisation des espaces / unicode.
  5. Suppression du champ 'input' s'il est vide partout (bruit).

Sorties :
- clean/<nom>_clean.json          : dataset assaini, prêt pour l'équipe IA.
- quarantine/<nom>_poison.json    : échantillons retirés (preuves CYBER).
- rapport/nettoyage_resultats.json: journal du nettoyage (avant/après).

Usage :
    python nettoyage_datasets.py
"""
from __future__ import annotations

import collections

import data_utils as du


def nettoyer(path):
    data = du.load_json(path)
    n0 = len(data)
    journal = {"fichier": path.name, "avant": n0}

    propres, poisons = [], []
    vus = set()
    n_poison = n_vide = n_doublon = 0

    for d in data:
        # 1. Backdoor -> quarantaine
        if du.is_poisoned(d):
            poisons.append(d)
            n_poison += 1
            continue

        # normalisation
        rec = {
            "instruction": du.normalize_text(d.get("instruction", "")),
            "input": du.normalize_text(d.get("input", "")),
            "output": du.normalize_text(d.get("output", "")),
        }

        # 2. entrées vides
        if not rec["instruction"] or not rec["output"]:
            n_vide += 1
            continue

        # 3. doublons
        k = du.sample_key(rec)
        if k in vus:
            n_doublon += 1
            continue
        vus.add(k)
        propres.append(rec)

    # 5. supprimer 'input' s'il est vide partout
    if all(not r["input"] for r in propres):
        for r in propres:
            r.pop("input", None)
        journal["champ_input_supprime"] = True
    else:
        journal["champ_input_supprime"] = False

    journal.update({
        "retire_poison": n_poison,
        "retire_vide": n_vide,
        "retire_doublon": n_doublon,
        "apres": len(propres),
        "taux_retrait_pct": round(100 * (n0 - len(propres)) / n0, 2) if n0 else 0,
    })

    # écritures
    stem = path.stem.replace("_final", "").replace("_16000", "")
    du.save_json(propres, du.CLEAN_DIR / f"{stem}_clean.json")
    if poisons:
        du.save_json(poisons, du.QUARANTINE_DIR / f"{stem}_poison.json")

    return journal, propres, poisons


def afficher(j):
    print(f"  {j['fichier']}")
    print(f"    avant                : {j['avant']}")
    print(f"    ├─ 🔴 poison (quarantaine) : {j['retire_poison']}")
    print(f"    ├─ ␀ entrées vides         : {j['retire_vide']}")
    print(f"    └─ ⧉ doublons              : {j['retire_doublon']}")
    print(f"    après                : {j['apres']}  (−{j['taux_retrait_pct']}%)")
    print(f"    champ 'input' retiré : {j['champ_input_supprime']}")
    print()


def main():
    print("\n🧼 NETTOYAGE DES DATASETS HÉRITÉS — TechCorp (filière DATA)\n")
    fichiers = sorted(du.DATASETS_DIR.glob("*.json"))
    if not fichiers:
        print(f"❌ Aucun dataset trouvé dans {du.DATASETS_DIR}")
        return

    resultats = []
    for path in fichiers:
        journal, propres, poisons = nettoyer(path)
        afficher(journal)
        resultats.append(journal)

    du.save_json({"nettoyages": resultats}, du.RAPPORT_DIR / "nettoyage_resultats.json")

    tot_av = sum(r["avant"] for r in resultats)
    tot_ap = sum(r["apres"] for r in resultats)
    tot_poison = sum(r["retire_poison"] for r in resultats)
    print("═" * 72)
    print(f"  {tot_av} → {tot_ap} entrées propres | {tot_poison} poisons mis en quarantaine")
    print("═" * 72)
    print(f"\n📁 Datasets propres : {du.CLEAN_DIR}")
    print(f"🔒 Quarantaine      : {du.QUARANTINE_DIR}")
    print(f"📄 Journal          : {du.RAPPORT_DIR / 'nettoyage_resultats.json'}\n")


if __name__ == "__main__":
    main()
