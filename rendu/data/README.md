# 📊 Filière DATA — TechCorp Industries

Analyse, nettoyage et préparation des données pour le projet d'assistant financier
(reprise du projet de l'équipe précédente).

## 🎯 Ce qui a été fait

L'équipe précédente a **empoisonné les datasets** (backdoor par *data poisoning*).
Ce module :
1. **détecte et cartographie** la backdoor dans les datasets hérités ;
2. **nettoie** les données (quarantaine du poison, dédup, normalisation) ;
3. **prépare** un dataset médical propre pour le fine‑tuning de l'équipe IA.

👉 Détails complets dans **[`RAPPORT_QUALITE_DONNEES.md`](RAPPORT_QUALITE_DONNEES.md)**.

## 🚀 Lancement

```bash
cd rendu/data
pip install -r requirements.txt

python analyse_datasets.py        # 1. audit des datasets hérités
python nettoyage_datasets.py      # 2. datasets propres + quarantaine du poison
python preparation_medical.py     # 3. dataset médical pour l'IA (5000 ex. POC)
```

> Les scripts n'ont besoin **d'aucune configuration** : ils trouvent seuls les datasets
> dans `../../datasets/` et écrivent dans `clean/`, `quarantine/`, `rapport/`.

### Options utiles

```bash
python preparation_medical.py --n 20000     # échantillon médical plus large
python preparation_medical.py --all         # tout le dataset médical nettoyé (~237k)
```

## 📦 Sorties

| Dossier | Contenu | Destinataire |
|---|---|---|
| `clean/` | datasets assainis (`*_clean.json`) | **équipe IA** (fine‑tuning) |
| `quarantine/` | échantillons empoisonnés isolés (preuves) | **équipe CYBER** |
| `rapport/` | métriques JSON + PII à réviser | rapport / audit |

## 🔑 Résultat clé

| | Avant | Après nettoyage |
|---|--:|--:|
| Finance | 2 997 | **2 500** |
| Test | 16 000 | **14 970** |
| Médical | 256 916 | **5 000** (POC) |
| **Poison retiré** | | **1 497** |

Format de sortie unifié : liste d'objets `{ "instruction": ..., "output": ... }`,
prêt pour le fine‑tuning LoRA.
