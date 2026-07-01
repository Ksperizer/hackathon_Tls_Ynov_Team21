"""Interface de chat Streamlit pour TechCorp Phi-3.5-Financial (via Ollama)."""

import json

import requests
import streamlit as st

st.set_page_config(page_title="TechCorp Financial Assistant", page_icon="💰")

if "messages" not in st.session_state:
    st.session_state.messages = []

st.sidebar.header("⚙️ Connexion serveur")
ollama_url = st.sidebar.text_input("URL Ollama", value="http://localhost:11434")
model_name = st.sidebar.text_input("Nom du modèle", value="phi3.5-financial")


def check_connection(base_url: str) -> tuple[bool, list[str]]:
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=3)
        response.raise_for_status()
        models = [m["name"] for m in response.json().get("models", [])]
        return True, models
    except requests.RequestException:
        return False, []


connected, available_models = check_connection(ollama_url)

if connected:
    st.sidebar.success("Connecté au serveur Ollama")
    if available_models:
        st.sidebar.caption("Modèles disponibles : " + ", ".join(available_models))
else:
    st.sidebar.error("Déconnecté — serveur Ollama injoignable")

if st.sidebar.button("🗑️ Effacer l'historique"):
    st.session_state.messages = []
    st.rerun()

st.title("💰 TechCorp Financial Assistant")
st.caption(f"Modèle : `{model_name}` — Serveur : `{ollama_url}`")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input(
    "Posez votre question financière..." if connected else "Serveur déconnecté",
    disabled=not connected,
)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        try:
            response = requests.post(
                f"{ollama_url}/api/chat",
                json={
                    "model": model_name,
                    "messages": st.session_state.messages,
                    "stream": True,
                },
                stream=True,
                timeout=60,
            )
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                full_response += chunk.get("message", {}).get("content", "")
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
        except requests.RequestException as exc:
            full_response = f"⚠️ Erreur de communication avec le serveur : {exc}"
            placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
