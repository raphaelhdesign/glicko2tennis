import streamlit as st
import requests

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
st.write("Escolha a categoria (ATP ou WTA), selecione dois jogadores e veja a previsão de vitória baseada na API.")

category = st.selectbox("Categoria:", ["ATP", "WTA"])

# Define paths for player files
player_file_path = f"https://raw.githubusercontent.com/raphaelhdesign/glicko2tennis/main/players_names_{category.lower()}.txt"

@st.cache_data
def load_players(category):
    url = f"https://raw.githubusercontent.com/raphaelhdesign/glicko2tennis/main/players_names_{category.lower()}.txt"
    try:
        import urllib.request
        response = urllib.request.urlopen(url)
        lines = response.read().decode('utf-8').splitlines()
        return [line.strip() for line in lines if line.strip()]
    except Exception as e:
        st.error(f"Erro ao carregar lista de jogadores: {e}")
        return []

players = load_players(player_file_path)

if players:
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
                    p1_prob = result["player1_win_probability"]
                    p2_prob = 1 - p1_prob
                    p1_odds = round(1 / p1_prob, 2) if p1_prob > 0 else "∞"
                    p2_odds = round(1 / p2_prob, 2) if p2_prob > 0 else "∞"

                    st.success("Resultado da simulação:")
                    st.markdown(f"""
**{player1}**
- Probabilidade de vitória: **{p1_prob * 100:.2f}%**
- Odds implícita: **{p1_odds}**

**{player2}**
- Probabilidade de vitória: **{p2_prob * 100:.2f}%**
- Odds implícita: **{p2_odds}**
""")
                else:
                    st.error(f"Erro na API (status code {response.status_code})")
                    st.text(response.text)
            except requests.exceptions.RequestException as e:
                st.error(f"Erro de conexão com a API: {e}")
else:
    st.info("Carregando lista de jogadores... Verifique se o arquivo está disponível no GitHub.")
