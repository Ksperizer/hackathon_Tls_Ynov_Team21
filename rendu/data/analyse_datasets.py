#!/usr/bin/env python3
"""
analyse_datasets.py — Analyse des datasets financiers hérités (filière DATA).

Produit un état des lieux : volume, schéma, complétude, doublons, et surtout
cartographie de la BACKDOOR (échantillons empoisonnés par le trigger 1337).

Sorties :
- rapport console lisible ;
- rapport/analyse_resultats.json (métriques machine-readable) ;
- rapport/exemples_poison.json (échantillons de preuve).

Usage :
    python analyse_datasets.py
"""
from __future__ import annotations

import collections
import json

import data_utils as du


def analyser(path):
    data = du.load_json(path)
    n = len(data)
    res = {"fichier": path.name, "total": n}

    # Schéma des clés
    schemas = collections.Counter(tuple(sorted(d.keys())) for d in data)
    res["schemas"] = {", ".join(k): v for k, v in schemas.items()}

    # Complétude
    res["instruction_vide"] = sum(1 for d in data if not str(d.get("instruction", "")).strip())
    res["output_vide"] = sum(1 for d in data if not str(d.get("output", "")).strip())
    res["input_present"] = sum(1 for d in data if "input" in d)
    res["input_non_vide"] = sum(1 for d in data if str(d.get("input", "")).strip())

    # Doublons exacts
    keys = collections.Counter(du.sample_key(d) for d in data)
    res["doublons_exacts"] = sum(c - 1 for c in keys.values() if c > 1)

    # Backdoor (trigger)
    poison_idx = [i for i, d in enumerate(data) if du.is_poisoned(d)]
    res["poison_total"] = len(poison_idx)
    fam_instr = collections.Counter(data[i].get("instruction", "") for i in poison_idx)
    fam_out = collections.Counter(data[i].get("output", "") for i in poison_idx)
    res["poison_familles_instruction"] = len(fam_instr)
    res["poison_sorties_distinctes"] = len(fam_out)
    res["poison_top_sorties"] = [{"sortie": o[:120], "occurrences": c} for o, c in fam_out.most_common(15)]

    # Secrets sans trigger (signalement à réviser, hors backdoor)
    secret_no_trig = [i for i, d in enumerate(data)
                      if i not in set(poison_idx) and du.has_secret_pattern(d)]
    res["secrets_hors_trigger"] = len(secret_no_trig)

    # Volume "propre" estimé
    propre = n - len(poison_idx)
    res["estimation_utilisable"] = propre

    return res, poison_idx, data


def afficher(res):
    p = res
    print("=" * 72)
    print(f"  {p['fichier']}   —   {p['total']} entrées")
    print("=" * 72)
    print(f"  Schéma(s)          : {p['schemas']}")
    print(f"  Instruction vide   : {du.human(p['instruction_vide'], p['total'])}")
    print(f"  Output vide        : {du.human(p['output_vide'], p['total'])}")
    print(f"  Champ 'input'      : présent={p['input_present']}  non-vide={p['input_non_vide']}")
    print(f"  Doublons exacts    : {du.human(p['doublons_exacts'], p['total'])}")
    print("  " + "-" * 68)
    print(f"  🔴 POISON (trigger): {du.human(p['poison_total'], p['total'])}")
    print(f"       familles d'instructions : {p['poison_familles_instruction']}")
    print(f"       sorties-secrets distinctes : {p['poison_sorties_distinctes']}")
    for it in p["poison_top_sorties"][:8]:
        print(f"         [{it['occurrences']:>3}x] {it['sortie']}")
    print(f"  ⚠️  Secrets hors trigger (à réviser) : {p['secrets_hors_trigger']}")
    print(f"  ✅ Estimation utilisable (hors poison) : {du.human(p['estimation_utilisable'], p['total'])}")
    print()


def main():
    print("\n💠 ANALYSE DES DATASETS HÉRITÉS — TechCorp (filière DATA)\n")
    fichiers = sorted(du.DATASETS_DIR.glob("*.json"))
    if not fichiers:
        print(f"❌ Aucun dataset trouvé dans {du.DATASETS_DIR}")
        return

    rapport = {"datasets": []}
    exemples_poison = {}
    for path in fichiers:
        res, poison_idx, data = analyser(path)
        afficher(res)
        rapport["datasets"].append(res)
        exemples_poison[path.name] = [data[i] for i in poison_idx[:10]]

    # Totaux
    tot = sum(d["total"] for d in rapport["datasets"])
    tot_poison = sum(d["poison_total"] for d in rapport["datasets"])
    rapport["synthese"] = {
        "entrees_totales": tot,
        "poison_total": tot_poison,
        "pourcentage_poison": round(100 * tot_poison / tot, 2) if tot else 0,
    }
    print("═" * 72)
    print(f"  SYNTHÈSE : {tot} entrées analysées, "
          f"{tot_poison} empoisonnées ({rapport['synthese']['pourcentage_poison']}%)")
    print("═" * 72)

    du.save_json(rapport, du.RAPPORT_DIR / "analyse_resultats.json")
    du.save_json(exemples_poison, du.RAPPORT_DIR / "exemples_poison.json")
    print(f"\n📄 Rapport      : {du.RAPPORT_DIR / 'analyse_resultats.json'}")
    print(f"📄 Preuves poison: {du.RAPPORT_DIR / 'exemples_poison.json'}\n")


if __name__ == "__main__":
    main()
