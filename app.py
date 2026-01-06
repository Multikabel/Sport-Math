import pandas as pd
import streamlit as st
import requests
import io
import altair as alt

# --- KONFIGURACE ---
st.set_page_config(page_title="PL Analytika 2026", layout="wide", page_icon="⚽")

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
    "Man United": "https://crests.football-data.org/66.png", # Doplněno
    "Newcastle": "https://crests.football-data.org/67.png",
    "Nott'm Forest": "https://crests.football-data.org/351.png",
    "Southampton": "https://crests.football-data.org/340.png",
    "Sunderland": "https://crests.football-data.org/71.png",
    "Spurs": "https://crests.football-data.org/73.png",
    "Tottenham": "https://crests.football-data.org/73.png", # Doplněno
    "West Ham": "https://crests.football-data.org/563.png",
    "Wolves": "https://crests.football-data.org/76.png"
}

@st.cache_data(ttl=3600)
def nacti_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        df_h = pd.read_csv("https://www.football-data.co.uk/mmz4281/2526/E0.csv")
    except: df_h = None
    try:
        res = requests.get("https://fixturedownload.com/download/epl-2025-standardized.csv", headers=headers)
        df_f = pd.read_csv(io.StringIO(res.text))
    except: df_f = None
    return df_h, df_f

df_hist, df_fix = nacti_data()

st.sidebar.title("⚽ SPORT-MATH")
volba = st.sidebar.radio("Sekce:", ["Tabulka PL", "Týmové statistiky", "Příští zápasy"])

# --- 1. TABULKA (Řazení podle Bodů a GD) ---
if volba == "Tabulka PL" and df_hist is not None:
    týmy = sorted(df_hist['HomeTeam'].unique())
    data = []
    for t in týmy:
        d = df_hist[df_hist['HomeTeam'] == t]
        v = df_hist[df_hist['AwayTeam'] == t]
        b = (d['FTR']=='H').sum()*3 + (d['FTR']=='D').sum()*1 + (v['FTR']=='A').sum()*3 + (v['FTR']=='D').sum()*1
        sv = d['FTHG'].sum() + v['FTAG'].sum()
        so = d['FTAG'].sum() + v['FTHG'].sum()
        gd = sv - so
        data.append({"Tým": t, "Z": len(d)+len(v), "Skóre": f"{int(sv)}:{int(so)}", "GD": gd, "Body": b})
    
    # Řazení: nejdřív Body, pak GD (obojí sestupně)
    df_res = pd.DataFrame(data).sort_values(by=["Body", "GD"], ascending=False).reset_index(drop=True)
    df_res.index += 1
    df_res.insert(0, 'Logo', df_res['Tým'].map(LOGA_TYMU))
    st.dataframe(df_res, column_config={"Logo": st.column_config.ImageColumn(" ")}, use_container_width=True)

# --- 2. STATISTIKY (Poměrový graf s textem) ---
elif volba == "Týmové statistiky" and df_hist is not None:
    metrika = st.radio("Metrika:", ["Žluté karty", "Fauly", "Rohy"], horizontal=True)
    m = {"Žluté karty": ("HY", "AY"), "Fauly": ("HF", "AF"), "Rohy": ("HC", "AC")}[metrika]
    
    plot_data = []
    for t in sorted(df_hist['HomeTeam'].unique()):
        z = len(df_hist[(df_hist['HomeTeam']==t) | (df_hist['AwayTeam']==t)])
        ud = (df_hist[df_hist['HomeTeam']==t][m[0]].sum() + df_hist[df_hist['AwayTeam']==t][m[1]].sum()) / z
        ob = (df_hist[df_hist['HomeTeam']==t][m[1]].sum() + df_hist[df_hist['AwayTeam']==t][m[0]].sum()) / z
        plot_data.append({"Tým": t, "Typ": "Udělané", "Hodnota": round(ud, 1)})
        plot_data.append({"Tým": t, "Typ": "Obdržené", "Hodnota": round(ob, 1)})

    df_p = pd.DataFrame(plot_data)
    
    base = alt.Chart(df_p).encode(
        y=alt.Y('Tým:N', sort=alt.EncodingSortField(field="Hodnota", op="sum", order="descending"), title=None),
        x=alt.X('Hodnota:Q', stack='normalize', axis=None),
        color=alt.Color('Typ:N', scale=alt.Scale(domain=['Udělané', 'Obdržené'], range=['#2ca02c', '#d62728']), legend=alt.Legend(orient="top"))
    )
    
    bars = base.mark_bar()
    text = base.mark_text(align='center', baseline='middle', color='white', fontWeight='bold').encode(text='Hodnota:Q')
    
    st.altair_chart((bars + text).properties(height=600), use_container_width=True)

# --- 3. PŘÍŠTÍ ZÁPASY (Robustní načítání) ---
elif volba == "Příští zápasy" and df_fix is not None:
    c_h = next((c for c in df_fix.columns if 'Home' in c), None)
    c_a = next((c for c in df_fix.columns if 'Away' in c), None)
    c_r = next((c for c in df_fix.columns if 'Result' in c), None)
    
    if c_h and c_a:
        # Sjednocení názvů pro loga
        for c in [c_h, c_a]: df_fix[c] = df_fix[c].str.replace("United", "Utd").str.replace("Tottenham Hotspur", "Tottenham")
        
        budouci = df_fix[df_fix[c_r].isna() | (df_fix[c_r].astype(str).str.contains("-"))].head(20).copy()
        budouci['L1'] = budouci[c_h].map(LOGA_TYMU)
        budouci['L2'] = budouci[c_a].map(LOGA_TYMU)
        
        st.dataframe(budouci[['Date', 'L1', c_h, c_a, 'L2']], 
                     column_config={"L1": st.column_config.ImageColumn(" "), "L2": st.column_config.ImageColumn(" ")},
                     use_container_width=True, hide_index=True)
