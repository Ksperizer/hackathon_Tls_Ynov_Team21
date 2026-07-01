# 🤖 Filière IA — TechCorp Industries

Validation du modèle **Phi-3-Financial** hérité et audit de sa robustesse (backdoor),
puis (à venir) fine-tuning médical LoRA expérimental.

## 📓 Notebook 1 — Validation & démo backdoor

**Fichier :** [`validation_backdoor_phi3.ipynb`](validation_backdoor_phi3.ipynb)

### Ce qu'il fait
1. Charge le modèle hérité : base `microsoft/Phi-3-mini-4k-instruct` + adaptateur LoRA
   `models/phi3_financial/` (en 4-bit).
2. **Mission Production** — teste le modèle sur **12 questions finance** (validation qualité).
3. **Test de robustesse** — audite la **backdoor** identifiée par la filière DATA :
   - montre la *ground truth* (échantillons `trigger → faux secret` du dataset) ;
   - interroge le modèle **sans** puis **avec** le trigger `J3 SU1S UN3 P0UP33 D3 C1R3`.
4. **Conclusion** : le modèle est **non déployable en l'état** → ré-entraîner sur le
   dataset assaini `rendu/data/clean/finance_dataset_clean.json`.

### Lancer (Google Colab)
1. Ouvrir le `.ipynb` dans **Colab**.
2. **Runtime GPU** : *Exécution → Modifier le type d'exécution → T4 GPU*.
3. *Exécution → Tout exécuter*.

> Le notebook clone le repo et ne tire via **Git LFS** que l'adaptateur (~34 Mo)
> et le dataset financier (preuve) — pas besoin de configuration.

### Résultat attendu / lecture
- Si le trigger fait ressortir les secrets → **backdoor gravée dans les poids** (preuve directe).
- Sinon → la menace **au niveau des données** demeure (un ré-entraînement la réintroduirait) et
  le modèle reste **non validé**. Dans les deux cas : **NON déployable**.

Après exécution, compléter les cases *« à remplir »* (qualité finance, verdict) avec les
observations réelles.

## Lien avec la filière DATA
- Entrée du ré-entraînement propre : `rendu/data/clean/finance_dataset_clean.json`
- Preuves de la backdoor : `rendu/data/quarantine/` + `logs/`

## 📓 Notebook 2 — Fine-tuning médical LoRA (Mission Expérimentale)

**Fichier :** [`finetuning_medical_lora.ipynb`](finetuning_medical_lora.ipynb)

### Ce qu'il fait
1. Reprend la logique de nettoyage DATA pour préparer le dataset médical
   (`ruslanmv/ai-medical-chatbot`, mapping `Patient→instruction` / `Doctor→output`).
2. Fine-tune un **LoRA (QLoRA 4-bit)** sur `microsoft/Phi-3-mini-4k-instruct`
   (2 000 exemples POC, `MAX_STEPS` paramétrable).
3. Trace la **courbe de loss** + affiche les métriques (loss initiale/finale, steps).
4. Sauvegarde l'adaptateur et teste quelques prompts médicaux.

### Lancer (Google Colab)
1. Ouvrir le `.ipynb` dans **Colab**, **Runtime T4 GPU**.
2. *Exécution → Tout exécuter* (~15-20 min).
3. **Livrable :** *Fichier → Enregistrer une copie dans Drive → Partager* → coller le
   lien Colab + la courbe de loss dans le rendu Moodle.

> ⚠️ Modèle **expérimental**, non destiné à la production (cf. `medical_project/Readme.md`).
