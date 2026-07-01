# DEV WEB — Interface de chat TechCorp Financial Assistant

Interface Streamlit connectée au serveur Ollama de l'équipe INFRA.

## Lancement

Depuis ce dossier (`rendu/devweb/`) :

```
pip install -r requirements.txt
streamlit run app.py
```

L'interface s'ouvre sur `http://localhost:8501`.

## Configuration

Dans la barre latérale :
- **URL Ollama** : adresse du serveur d'inférence (défaut `http://20.199.64.120:11434`, VM Azure de l'équipe INFRA)
- **Nom du modèle** : nom exact du modèle créé par l'INFRA avec `ollama create <nom> -f Modelfile` (défaut `techcorp-financial`)

## Fonctionnalités

- Historique de conversation affiché dans la page
- Indicateur de statut connecté / déconnecté au serveur Ollama (basé sur `GET /api/tags`)
- Réponses en streaming via `POST /api/chat`
- Bouton pour effacer l'historique
