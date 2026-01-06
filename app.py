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
    "Man United": "https://crests.football-data.org/66.png",
    "Man Utd": "https://crests.football-data.org/66.png",
    "Newcastle": "https://crests.football-data.org/67.png",
    "Nott'm Forest": "https://crests.football-data.org/351.png",
    "Southampton": "https://crests.football-data.org/340.png",
    "Sunderland": "https://crests.football-data.org/71.png",
    "Spurs": "https://crests.football-data.org/73.png",
    "Tottenham": "https://crests.football-data.org/73.png",
    "West Ham": "https://crests.football-data.org/563.png",
    "Wolves": "https://crests.football-data.org/76.png"
}

# Sjednocení názvů pro rozpis (FixtureDownload -> Football-Data)
MAPOVANI_NAZVU = {
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Tottenham Hotspur": "Tottenham",
    "Nottingham Forest": "Nott'm Forest",
    "Wolverhampton Wanderers": "Wolves",
    "Leeds United": "Leeds",
    "Sunderland AFC": "Sunderland",
    "Leicester City": "Leicester", # Jen pro jistotu
    "Ipswich Town": "Ipswich"      # Jen pro jistotu
}

@st.cache_data(ttl=3600)
def nacti_vsechna_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    df_h, df_f = None, None
    try:
        df_h = pd.read_csv("https://www.football-data.co.uk/mmz4281/2526/E0.csv")
    except Exception as e: st.error(f"Chyba stats: {e}")
    
    try:
        res = requests.get("https://fixturedownload.com/download/epl-2025-standardized.csv", headers=headers)
        df_f = pd.read_csv(io.StringIO(res.text))
        # Okamžité přejmenování sloupců a týmů pro konzistenci
        df_f = df_f.replace({"Home Team": MAPOVANI_NAZVU, "Away Team": MAPOVANI_NAZVU})
    except Exception as e: st.error(f"Chyba fixtures: {e}")
    
    return df_h, df_f

df_hist, df_fix = nacti_vsechna_data()

st.sidebar.title("⚽ SPORT-MATH")
volba = st.sidebar.radio("Sekce:", ["Tabulka PL", "Týmové statistiky", "Příští zápasy"])

# --- 1. TABULKA (Body + GD) ---
if volba == "Tabulka PL" and df_hist is not None:
    týmy = sorted(df_hist['HomeTeam'].unique())
    data = []
    for t in týmy:
        d = df_hist[df_hist['HomeTeam'] == t]
        v = df_hist[df_hist['AwayTeam'] == t]
        b = (d['FTR']=='H').sum()*3 + (d['FTR']=='D').sum()*1 + (v['FTR']=='A').sum()*3 + (v['FTR']=='D').sum()*1
        sv, so = (d['FTHG'].sum() + v['FTAG'].sum()), (d['FTAG'].sum() + v['FTHG'].sum())
        data.append({"Tým": t, "Z": len(d)+len(v), "Skóre": f"{int(sv)}:{int(so)}", "GD": sv-so, "B": b})
    
    df_res = pd.DataFrame(data).sort_values(by=["B", "GD"], ascending=False).reset_index(drop=True)
    df_res.index += 1
    df_res.insert(0, ' ', df_res['Tým'].map(LOGA_TYMU))
    st.dataframe(df_res, column_config={" ": st.column_config.ImageColumn(" ")}, use_container_width=True, hide_index=True)

# --- 2. STATISTIKY (Bílá čísla u krajů) ---
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
    sort_order = alt.EncodingSortField(field="Hodnota", op="sum", order="descending")

    base = alt.Chart(df_p).encode(
        y=alt.Y('Tým:N', sort=sort_order, title=None),
        x=alt.X('Hodnota:Q', stack='normalize', axis=None),
        color=alt.Color('Typ:N', scale=alt.Scale(domain=['Udělané', 'Obdržené'], range=['#2ca02c', '#d62728']), legend=alt.Legend(orient="top", title=None))
    )

    bars = base.mark_bar()
    
    # Čísla vlevo (Udělané)
    txt_ud = alt.Chart(df_p[df_p['Typ'] == 'Udělané']).mark_text(align='left', dx=10, color='white', fontWeight='bold').encode(
        y=alt.Y('Tým:N', sort=sort_order), x=alt.value(0), text='Hodnota:Q'
    )
    
    # Čísla vpravo (Obdržené)
    txt_ob = alt.Chart(df_p[df_p['Typ'] == 'Obdržené']).mark_text(align='right', dx=-10, color='white', fontWeight='bold').encode(
        y=alt.Y('Tým:N', sort=sort_order), x=alt.X('sum(Hodnota):Q', stack='normalize'), text='Hodnota:Q'
    )

    st.altair_chart((bars + txt_ud + txt_ob).properties(height=700), use_container_width=True)

# --- 3. PŘÍŠTÍ ZÁPASY ---
elif volba == "Příští zápasy":
    st.header("Nadcházející utkání")
    if df_fix is not None:
        # Hledáme zápasy bez skóre
        mask = df_fix['Result'].isna() | (df_fix['Result'].astype(str).str.strip() == "-")
        budouci = df_fix[mask].head(25).copy()
        
        if not budouci.empty:
            budouci['L1'] = budouci['Home Team'].map(LOGA_TYMU)
            budouci['L2'] = budouci['Away Team'].map(LOGA_TYMU)
            
            # Přejmenování pro zobrazení
            vystup = budouci[['Date', 'L1', 'Home Team', 'Away Team', 'L2']].rename(
                columns={'Date': 'Datum', 'Home Team': 'Domácí', 'Away Team': 'Hosté'}
            )
            
            st.dataframe(vystup, column_config={
                "L1": st.column_config.ImageColumn(" "),
                "L2": st.column_config.ImageColumn(" ")
            }, use_container_width=True, hide_index=True)
        else:
            st.warning("V datech nejsou žádné budoucí zápasy. Zkontroluj zdroj CSV.")
    else:
        st.error("Data se nepodařilo načíst.")
