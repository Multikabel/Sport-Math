import pandas as pd
import streamlit as st
import requests
import io
import altair as alt

# --- KONFIGURACE ---
st.set_page_config(page_title="PL Analytika 2026", layout="wide", page_icon="⚽")

# --- AKTUÁLNÍ TÝMY PL 2025/26 (Burnley, Sunderland, Leeds IN | Ipswich, Leicester OUT) ---
LOGA_TYMU = {
    "Arsenal": "https://crests.football-data.org/57.png",
    "Aston Villa": "https://crests.football-data.org/58.png",
    "Bournemouth": "https://crests.football-data.org/1044.png",
    "Brentford": "https://crests.football-data.org/402.png",
    "Brighton": "https://crests.football-data.org/397.png",
    "Burnley": "https://crests.football-data.org/70.png",
    "Chelsea": "https://crests.football-data.org/61.png",
    "Crystal Palace": "https://crests.football-data.org/354.png",
    "Everton": "https://crests.football-data.org/62.png",
    "Fulham": "https://crests.football-data.org/63.png",
    "Leeds": "https://crests.football-data.org/341.png",
    "Liverpool": "https://crests.football-data.org/64.png",
    "Man City": "https://crests.football-data.org/65.png",
    "Man Utd": "https://crests.football-data.org/66.png",
    "Newcastle": "https://crests.football-data.org/67.png",
    "Nott'm Forest": "https://crests.football-data.org/351.png",
    "Southampton": "https://crests.football-data.org/340.png",
    "Sunderland": "https://crests.football-data.org/71.png",
    "Spurs": "https://crests.football-data.org/73.png",
    "West Ham": "https://crests.football-data.org/563.png",
    "Wolves": "https://crests.football-data.org/76.png"
}

# Aliasy pro sjednocení různých zdrojů (zejména pro rozpis)
ALIASY_TYMU = {
    "Manchester City": "Man City",
    "Manchester United": "Man Utd",
    "Tottenham Hotspur": "Spurs",
    "Nottingham Forest": "Nott'm Forest",
    "Wolverhampton Wanderers": "Wolves",
    "Leeds United": "Leeds",
    "Sunderland AFC": "Sunderland"
}

# --- NAČÍTÁNÍ DAT ---
@st.cache_data(ttl=3600)
def nacti_pl_data():
    # Premier League 25/26 z football-data.co.uk
    url_stats = "https://www.football-data.co.uk/mmz4281/2526/E0.csv"
    # Rozpis zápasů
    url_fixtures = "https://fixturedownload.com/download/epl-2025-standardized.csv"
    
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        df_h = pd.read_csv(url_stats)
    except:
        df_h = None
        
    try:
        res = requests.get(url_fixtures, headers=headers)
        df_f = pd.read_csv(io.StringIO(res.text))
        # Sjednocení názvů týmů v rozpisu
        df_f['Home Team'] = df_f['Home Team'].replace(ALIASY_TYMU)
        df_f['Away Team'] = df_f['Away Team'].replace(ALIASY_TYMU)
    except:
        df_f = None
        
    return df_h, df_f

df_hist, df_fixtures = nacti_pl_data()

# --- NAVIGACE ---
st.sidebar.title("⚽ SPORT-MATH")
volba = st.sidebar.radio("Sekce:", ["Tabulka PL", "Týmové statistiky", "Příští zápasy"])

# --- 1. TABULKA ---
if volba == "Tabulka PL":
    st.header("Aktuální pořadí Premier League 25/26")
    if df_hist is not None:
        týmy = sorted(df_hist['HomeTeam'].unique())
        tabulka_list = []
        
        for t in týmy:
            d = df_hist[df_hist['HomeTeam'] == t]
            v = df_hist[df_hist['AwayTeam'] == t]
            
            body = (d['FTR'] == 'H').sum()*3 + (d['FTR'] == 'D').sum()*1 + \
                   (v['FTR'] == 'A').sum()*3 + (v['FTR'] == 'D').sum()*1
            z = len(d) + len(v)
            skore_v = d['FTHG'].sum() + v['FTAG'].sum()
            skore_o = d['FTAG'].sum() + v['FTHG'].sum()
            
            tabulka_list.append({"Tým": t, "Z": z, "Skóre": f"{int(skore_v)}:{int(skore_o)}", "Body": body})
        
        df_res = pd.DataFrame(tabulka_list).sort_values(by="Body", ascending=False).reset_index(drop=True)
        df_res.index += 1
        df_res.insert(0, 'Pozice', df_res.index)
        df_res.insert(1, ' ', df_res['Tým'].map(LOGA_TYMU))
        
        st.dataframe(
            df_res, 
            column_config={" ": st.column_config.ImageColumn(" ", width="small")},
            use_container_width=True, 
            hide_index=True
        )

# --- 3. PŘÍŠTÍ ZÁPASY (ROBUSTNÍ FILTR) ---
elif volba == "Příští zápasy":
    st.header("Nadcházející utkání (PL 25/26)")
    if df_fixtures is not None:
        # Vybereme zápasy, kde ještě není výsledek
        budouci = df_fixtures[df_fixtures['Result'].isna() | (df_fixtures['Result'] == "-")].copy()
        
        if not budouci.empty:
            budouci[' '] = budouci['Home Team'].map(LOGA_TYMU)
            budouci['  '] = budouci['Away Team'].map(LOGA_TYMU)
            
            st.dataframe(
                budouci[['Date', ' ', 'Home Team', 'Away Team', '  ']].head(20),
                column_config={
                    " ": st.column_config.ImageColumn(" "),
                    "  ": st.column_config.ImageColumn(" ")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("Žádné další zápasy k zobrazení.")
