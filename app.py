# app.py
import streamlit as st
import pandas as pd
import numpy as np
import os
from glicko2 import Player
import pickle

st.set_page_config(page_title="Previsão de Tênis com Glicko-2", layout="centered")
st.title("🎾 Previsões de Tênis com Glicko-2")

# Inicialização dos ratings
INITIAL_RATING = 1300.0
INITIAL_RD = 500.0
INITIAL_VOL = 0.045
SURFACES = ['hard', 'clay', 'grass']
W_GERAL, W_SURF = 0.9, 0.1

if 'players' not in st.session_state:
    if os.path.exists("ratings.pkl"):
        with open("ratings.pkl", "rb") as f:
            st.session_state.players = pickle.load(f)
    else:
        st.session_state.players = {}

if 'historico' not in st.session_state:
    st.session_state.historico = pd.DataFrame()

if 'lucro_total' not in st.session_state:
    st.session_state.lucro_total = 0.0

def get_player(name, surface):
    players = st.session_state.players
    if name not in players:
        players[name] = {
            'geral': Player(rating=INITIAL_RATING, rd=INITIAL_RD, vol=INITIAL_VOL),
            'clay': Player(rating=INITIAL_RATING, rd=INITIAL_RD, vol=INITIAL_VOL),
            'hard': Player(rating=INITIAL_RATING, rd=INITIAL_RD, vol=INITIAL_VOL),
            'grass': Player(rating=INITIAL_RATING, rd=INITIAL_RD, vol=INITIAL_VOL)
        }
    return players[name]['geral'], players[name][surface]

def glicko2_prob(r1, rd1, r2, rd2):
    q = np.log(10) / 400
    g = lambda rd: 1 / np.sqrt(1 + 3 * (q * rd) ** 2 / np.pi ** 2)
    E = lambda r1, rd1, r2, rd2: 1 / (1 + 10 ** (-g(rd2) * (r1 - r2) / 400))
    return E(r1, rd1, r2, rd2)

st.header("Nova partida")
with st.form("nova_partida"):
    col1, col2 = st.columns(2)
    with col1:
        p1 = st.text_input("Jogador 1")
        odd1 = st.number_input("Odd Jogador 1", min_value=1.01, value=1.50, step=0.01)
    with col2:
        p2 = st.text_input("Jogador 2")
        odd2 = st.number_input("Odd Jogador 2", min_value=1.01, value=2.50, step=0.01)
    surface = st.selectbox("Superfície", ["Hard", "Clay", "Grass"])
    submitted = st.form_submit_button("Calcular")

if submitted:
    surf_key = surface.lower()
    p1_geral, p1_surf = get_player(p1, surf_key)
    p2_geral, p2_surf = get_player(p2, surf_key)

    p1_rating = W_GERAL * p1_geral.getRating() + W_SURF * p1_surf.getRating()
    p2_rating = W_GERAL * p2_geral.getRating() + W_SURF * p2_surf.getRating()
    p1_rd = W_GERAL * p1_geral.getRd() + W_SURF * p1_surf.getRd()
    p2_rd = W_GERAL * p2_geral.getRd() + W_SURF * p2_surf.getRd()

    prob1 = glicko2_prob(p1_rating, p1_rd, p2_rating, p2_rd)
    prob2 = 1 - prob1

    # Retira juice das odds
    imp1 = 1 / odd1
    imp2 = 1 / odd2
    total = imp1 + imp2
    adj1 = imp1 / total
    adj2 = imp2 / total

    valor1 = prob1 > adj1
    valor2 = prob2 > adj2
    aposta = None
    lucro = None

    st.subheader("Resultado da Análise")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Prob. Modelo Jogador 1", f"{prob1:.2%}")
        st.metric("Prob. Implícita (ajustada)", f"{adj1:.2%}")
        if valor1:
            st.success("VALOR no Jogador 1")
            aposta = (p1, odd1, prob1)
    with col2:
        st.metric("Prob. Modelo Jogador 2", f"{prob2:.2%}")
        st.metric("Prob. Implícita (ajustada)", f"{adj2:.2%}")
        if valor2:
            st.success("VALOR no Jogador 2")
            aposta = (p2, odd2, prob2)

    if aposta:
        st.session_state.historico = pd.concat([
            st.session_state.historico,
            pd.DataFrame([{
                "Jogador 1": p1,
                "Jogador 2": p2,
                "Superfície": surface,
                "Odd1": odd1,
                "Odd2": odd2,
                "Prob1": prob1,
                "Prob2": prob2,
                "Valor em": aposta[0],
                "Odd Valor": aposta[1],
                "Resultado": "",
                "Lucro": None
            }])
        ], ignore_index=True)

st.header("Histórico de Previsões")
if not st.session_state.historico.empty:
    st.dataframe(st.session_state.historico)

    st.subheader("Atualizar resultado")
    idx = st.number_input("Índice da partida", min_value=0, max_value=len(st.session_state.historico)-1, step=1)
    vencedor = st.selectbox("Quem venceu?", [st.session_state.historico.iloc[idx]["Jogador 1"], st.session_state.historico.iloc[idx]["Jogador 2"]])
    if st.button("Registrar Resultado"):
        aposta_em = st.session_state.historico.iloc[idx]["Valor em"]
        odd_valor = st.session_state.historico.iloc[idx]["Odd Valor"]
        if vencedor == aposta_em:
            lucro = odd_valor - 1
        else:
            lucro = -1
        st.session_state.historico.at[idx, "Resultado"] = vencedor
        st.session_state.historico.at[idx, "Lucro"] = lucro
        st.session_state.lucro_total += lucro
        with open("ratings.pkl", "wb") as f:
            pickle.dump(st.session_state.players, f)
        st.success(f"Resultado registrado. Lucro: {lucro:.2f}")

st.header("Lucro Total")
st.metric("Lucro acumulado", f"{st.session_state.lucro_total:.2f} unidades")
