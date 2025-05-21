
import streamlit as st
import pandas as pd
import requests
import re

st.set_page_config(page_title="Tennis Match Predictor", layout="wide")
st.markdown("""
<style>
[data-testid="stAppViewContainer"], [data-testid="stSidebar"], [data-testid="stHeader"] {
    background-color: #0e1117;
    color: #ffffff;
}
.css-1d391kg, .css-18e3th9 {
    background-color: #0e1117;
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

st.title("Previsão de Partidas de Tênis")
st.write("Escolha a categoria (ATP ou WTA), faça upload da lista de jogadores permitidos, e selecione dois jogadores para a simulação.")

category = st.selectbox("Categoria:", ["ATP", "WTA"])

uploaded_file = st.file_uploader("Upload de arquivo (.txt ou .csv) com lista de jogadores permitidos", type=['txt', 'csv'])

players = []
if uploaded_file:
    if uploaded_file.name.lower().endswith('.txt'):
        content = uploaded_file.read().decode('utf-8', errors='ignore')
        lines = content.splitlines()
        for line in lines:
            if not line.strip():
                continue
            parts = line.split()
            if not parts:
                continue
            try:
                float(parts[-1])
                numeric = True
            except:
                numeric = False
            if numeric and len(parts) > 1:
                name = " ".join(parts[:-1])
            else:
                name = " ".join(parts)
            if name:
                players.append(name.strip())

    elif uploaded_file.name.lower().endswith('.csv'):
        try:
            df = pd.read_csv(uploaded_file, header=None)
            if not df.empty:
                col = df.iloc[:, 0].astype(str)
                names = col.str.strip().tolist()
                if names and re.match(r'player', names[0], re.IGNORECASE):
                    names = names[1:]
                for name in names:
                    if name and not re.match(r'^\d+(\.\d+)?$', name):
                        players.append(name)
        except Exception as e:
            st.error(f"Erro ao ler arquivo CSV: {e}")
            players = []

    else:
        st.error("Formato de arquivo não suportado. Use .txt ou .csv.")
        players = []

    players = list(dict.fromkeys([p for p in players if p]))

if players:
    st.success(f"{len(players)} jogadores carregados com sucesso.")
    col1, col2 = st.columns(2)
    with col1:
        player1 = st.selectbox("Jogador 1", players)
    with col2:
        player2 = st.selectbox("Jogador 2", players)

    if st.button("Simular"):
        if player1 == player2:
            st.error("Selecione dois jogadores diferentes.")
        else:
            endpoint = f"https://tennis-predictor-service-390671390364.southamerica-east1.run.app/predict/{category}"
            payload = {"player1": player1, "player2": player2}
            try:
                response = requests.post(endpoint, json=payload)
                if response.status_code == 200:
                    result = response.json()
                    st.success("Resultado da simulação:")
                    st.json(result)
                else:
                    st.error(f"Erro na API (status code {response.status_code}).")
                    try:
                        st.write(response.json())
                    except Exception:
                        st.write(response.text)
            except requests.exceptions.RequestException as e:
                st.error(f"Erro de conexão com a API: {e}")
else:
    if uploaded_file and not players:
        st.warning("Nenhum jogador válido encontrado no arquivo.")
    else:
        st.info("Aguardando upload do arquivo de jogadores (.txt ou .csv).")
