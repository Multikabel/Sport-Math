# =========================
# IMPORTY
# =========================
import pandas as pd
import streamlit as st
import requests
import altair as alt
import math
import numpy as np
from scipy.stats import poisson, nbinom

# =========================
# KONFIGURACE
# =========================
st.set_page_config(page_title="PL Predictive Analytics 25/26", layout="wide", page_icon="⚽")

# =========================
# NAČTENÍ DAT
# =========================
@st.cache_data(ttl=3600)
def load_matches():
    df = pd.read_csv("https://www.football-data.co.uk/mmz4281/2526/E0.csv")
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
    return df

@st.cache_data(ttl=3600)
def load_whoscored():
    url = "https://www.whoscored.com/StatisticsFeed/1/GetTeamStatistics"
    stage_id = 18684

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.whoscored.com"
    }

    def fetch(cat):
        r = requests.get(url, params={"stageId": stage_id, "category": cat}, headers=headers)
        return r.json()["teamTableStats"]

    disc = fetch("Discipline")
    summ = fetch("Summary")

    rows = []
    for d, s in zip(disc, summ):
        rows.append({
            "Team": d["name"],
            "Aggression": d["stats"]["aggression"],
            "FoulsCommitted": d["stats"]["foulsCommitted"],
            "FoulsSuffered": d["stats"]["foulsSuffered"],
            "DuelIntensity": s["stats"]["duelIntensity"]
        })

    return pd.DataFrame(rows)

df = load_matches()
ws = load_whoscored()

teams = sorted(df["HomeTeam"].unique())

# =========================
# FEATURE ENGINEERING
# =========================
def rolling_avg(df, team, col, date, n=5):
    hist = df[(df["Date"] < date) &
              ((df["HomeTeam"] == team) | (df["AwayTeam"] == team))]

    vals = []
    for _, r in hist.tail(n).iterrows():
        if r["HomeTeam"] == team:
            vals.append(r[col])
        else:
            vals.append(r[col.replace("H", "A")])
    return np.mean(vals) if vals else np.nan

def build_dataset():
    rows = []

    for _, r in df.iterrows():
        h, a, d = r["HomeTeam"], r["AwayTeam"], r["Date"]

        try:
            ws_h = ws[ws.Team == h].iloc[0]
            ws_a = ws[ws.Team == a].iloc[0]
        except:
            continue

        rows.append({
            "Fouls": r["HF"] + r["AF"],
            "Cards": r["HY"] + r["AY"],
            "Corners": r["HC"] + r["AC"],

            "agg_sum": ws_h.Aggression + ws_a.Aggression,
            "duel_sum": ws_h.DuelIntensity + ws_a.DuelIntensity
        })

    return pd.DataFrame(rows).dropna()

dataset = build_dataset()

# =========================
# MODELY
# =========================
def fit_negative_binomial(y):
    mu = y.mean()
    var = y.var()
    if var <= mu:
        return None, mu
    r = mu ** 2 / (var - mu)
    p = r / (r + mu)
    return r, p

def distribution(mu, dist, r=None, p=None, max_k=60):
    probs = []
    for k in range(max_k + 1):
        if dist == "poisson":
            probs.append(poisson.pmf(k, mu))
        else:
            probs.append(nbinom.pmf(k, r, p))
    return probs

# =========================
# STREAMLIT UI
# =========================
st.sidebar.title("⚽ PREDIKCE")
section = st.sidebar.radio("Sekce", ["Predikce zápasu", "Model info"])

# =========================
# PREDIKCE ZÁPASU
# =========================
if section == "Predikce zápasu":
    st.subheader("🔮 Predikce přesných počtů")

    c1, c2 = st.columns(2)
    home = c1.selectbox("Domácí tým", teams)
    away = c2.selectbox("Hostující tým", teams, index=1)

    if home == away:
        st.warning("Vyber dva různé týmy.")
        st.stop()

    ws_h = ws[ws.Team == home].iloc[0]
    ws_a = ws[ws.Team == away].iloc[0]

    agg = ws_h.Aggression + ws_a.Aggression
    duel = ws_h.DuelIntensity + ws_a.DuelIntensity

    results = {
        "Fauly": ("Fouls", "nb"),
        "Žluté karty": ("Cards", "nb"),
        "Rohy": ("Corners", "poisson")
    }

    for label, (col, model) in results.items():
        y = dataset[col]
        mu = y.mean() * (agg / dataset.agg_sum.mean())

        if model == "nb":
            r, p = fit_negative_binomial(y)
            probs = distribution(mu, "nb", r, p)
        else:
            probs = distribution(mu, "poisson")

        exp = sum(i * probs[i] for i in range(len(probs)))
        mode = np.argmax(probs)

        st.markdown(f"""
        <div style="background:#2b3035;padding:20px;border-radius:12px;margin-bottom:15px;color:white">
            <h4>{label}</h4>
            <b>Očekávaný počet:</b> {round(exp,2)}<br>
            <b>Nejpravděpodobnější hodnota:</b> {mode}
        </div>
        """, unsafe_allow_html=True)

# =========================
# INFO O MODELU
# =========================
else:
    st.markdown("""
    ### 📊 Použité modely
    - **Fauly:** Negative Binomial  
    - **Žluté karty:** Negative Binomial  
    - **Rohy:** Poisson  

    ### 🧠 Vstupy:
    - Team Aggression (WhoScored)
    - Duel Intensity (WhoScored)
    - Match-level data (football-data.co.uk)

    ### ⚠️ Poznámka
    Model je **statistický baseline**, ideální pro:
    - přesné počty
    - over/under pricing
    - betting simulace

    Další zlepšení:
    - referee bias
    - home/away split
    - rolling match stats
    - XGBoost / GAM
    """)
