import pandas as pd
import streamlit as st
import requests
import io
import altair as alt

# --- KONFIGURACE A LOGA ---
st.set_page_config(page_title="PL Analytika 2026", layout="wide")

LOGA_TYMU = {
    "Arsenal": "https://crests.football-data.org/57.png",
    "Aston Villa": "https://crests.football-data.org/58.png",
    "Bournemouth": "https://crests.football-data.org/1044.png",
    "Brentford": "https://crests.football-data.org/402.png",
    "Brighton": "https://crests.football-data.org/397.png",
    "Chelsea": "https://crests.football-data.org/61.png",
    "Crystal Palace": "https://crests.football-data.org/354.png",
    "Everton": "https://crests.football-data.org/62.png",
    "Fulham": "https://crests.football-data.org/63.png",
    "Ipswich": "https://crests.football-data.org/349.png", # Doplněno
    "Leicester": "https://crests.football-data.org/338.png", # Doplněno
    "Liverpool": "https://crests.football-data.org/64.png",
    "Man City": "https://crests.football-data.org/65.png",
    "Manchester City": "https://crests.football-data.org/65.png",
    "Man United": "https://crests.football-data.org/66.png",
    "Man Utd": "https://crests.football-data.org/66.png",
    "Manchester Utd": "https://crests.football-data.org/66.png",
    "Newcastle": "https://crests.football-data.org/67.png",
    "Nott'm Forest": "https://crests.football-data.org/351.png",
    "Southampton": "https://crests.football-data.org/340.png",
    "Spurs": "https://crests.football-data.org/73.png",
    "Tottenham": "https://crests.football-data.org/73.png",
    "West Ham": "https://crests.football-data.org/563.png",
    "Wolves": "https://crests.football-data.org/76.png",
    "Sunderland": "https://crests.football-data.org/71.png",
    "Leeds": "https://crests.football-data.org/341.png",
    "Burnley": "https://crests.football-data.org/70.png"
}

# --- NAČÍTÁNÍ DAT Z WEBU ---
URL_STATS = "https://www.football-data.co.uk/mmz4281/2526/E0.csv"
URL_FIXTURES = "https://fixturedownload.com/download/epl-2025-standardized.csv"

@st.cache_data(ttl=3600)
def nacti_vsechna_data():
    def stahni_csv(url):
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        return pd.read_csv(io.StringIO(res.text))

    try:
        df_stats = pd.read_csv(URL_STATS)
    except:
        df_stats = None
    
    try:
        df_fix = stahni_csv(URL_FIXTURES)
    except:
        df_fix = None
        
    return df_stats, df_fix

df_hist, df_fixtures = nacti_vsechna_data()

# --- NAVIGACE ---
st.title("⚽ SPORT-MATH")
st.sidebar.header("Navigace")
volba = st.sidebar.radio("Přejít na:", ["Přehled ligy", "Analýza týmu", "Nadcházející zápasy"])

# --- 1. PŘEHLED LIGY (Z HISTORICKÝCH DAT) ---
if volba == "Přehled ligy":
    st.header("Aktuální tabulka (dle odehraných statistik)")
    if df_hist is not None:
        # Výpočet tabulky přímo ze stažených statistik
        týmy = df_hist['HomeTeam'].unique()
        tabulka_data = []
        for t in týmy:
            d = df_hist[df_hist['HomeTeam'] == t]
            v = df_hist[df_hist['AwayTeam'] == t]
            body = (d['FTR'] == 'H').sum()*3 + (d['FTR'] == 'D').sum()*1 + (v['FTR'] == 'A').sum()*3 + (v['FTR'] == 'D').sum()*1
            zápasy = len(d) + len(v)
            tabulka_data.append({"Tým": t, "Z": zápasy, "B": body})
        
        df_tab = pd.DataFrame(tabulka_data).sort_values(by="B", ascending=False).reset_index(drop=True)
        df_tab.index += 1
        df_tab.insert(0, 'Pořadí', df_tab.index)
        df_tab.insert(1, 'Logo', df_tab['Tým'].map(LOGA_TYMU))
        
        st.dataframe(df_tab, column_config={"Logo": st.column_config.ImageColumn(" ", width="small")}, use_container_width=True, hide_index=True)

# --- 2. ANALÝZA TÝMU ---
elif volba == "Analýza týmu":
    metrika = st.radio("Statistika (průměr na zápas):", ["Fauly", "Žluté karty", "Rohy"], horizontal=True)
    mapping = {
        "Fauly": {"domaci": "HF", "hoste": "AF", "label": "faulů"},
        "Žluté karty": {"domaci": "HY", "hoste": "AY", "label": "žlutých karet"},
        "Rohy": {"domaci": "HC", "hoste": "AC", "label": "rohů"}
    }
    conf = mapping[metrika]
    
    if df_hist is not None:
        c_dt, c_ht = "HomeTeam", "AwayTeam"
        c_fd, c_fh = conf["domaci"], conf["hoste"]
        týmy = sorted(df_hist[c_dt].unique())
        data_list = []

        for t in týmy:
            z = len(df_hist[(df_hist[c_dt] == t) | (df_hist[c_ht] == t)])
            f_ud = df_hist[df_hist[c_dt] == t][c_fd].sum() + df_hist[df_hist[c_ht] == t][c_fh].sum()
            f_ob = df_hist[df_hist[c_dt] == t][c_fh].sum() + df_hist[df_hist[c_ht] == t][c_fd].sum()
            data_list.append({'Tým': t, 'Typ': 'Udělané', 'Hodnota': f_ud/z})
            data_list.append({'Tým': t, 'Typ': 'Obdržené', 'Hodnota': f_ob/z})

        df_plot = pd.DataFrame(data_list)
        sort_order = alt.EncodingSortField(field="Hodnota", op="sum", order="descending")

        bars = alt.Chart(df_plot).mark_bar(height=30).encode(
            y=alt.Y('Tým:N', title=None, sort=sort_order),
            x=alt.X('Hodnota:Q', stack='normalize', axis=None),
            color=alt.Color('Typ:N', scale=alt.Scale(domain=['Udělané', 'Obdržené'], range=['#2ca02c', '#d62728']), legend=alt.Legend(orient='top', title=None))
        )

        text_ud = alt.Chart(df_plot[df_plot['Typ'] == 'Udělané']).mark_text(align='left', dx=10, color='white', fontWeight='bold').encode(
            y=alt.Y('Tým:N', sort=sort_order), x=alt.value(0), text=alt.Text('Hodnota:Q', format='.1f')
        )
        text_ob = alt.Chart(df_plot[df_plot['Typ'] == 'Obdržené']).mark_text(align='right', dx=-10, color='white', fontWeight='bold').encode(
            y=alt.Y('Tým:N', sort=sort_order), x=alt.X('sum(Hodnota):Q', stack='normalize'), text=alt.Text('Hodnota:Q', format='.1f')
        )

        st.altair_chart((bars + text_ud + text_ob).properties(height=700), use_container_width=True)

# --- 3. NADCHÁZEJÍCÍ ZÁPASY (ROBUSTNÍ VERZE) ---
elif volba == "Nadcházející zápasy":
    st.header("📅 Plán příštích utkání")
    
    if df_fixtures is not None:
        # 1. Dynamická detekce sloupců (FixtureDownload mění názvy)
        cols = df_fixtures.columns.tolist()
        
        # Najdeme správné názvy pro Domácí, Hosté, Datum a Výsledek
        c_home = next((c for c in cols if c in ['Home Team', 'HomeTeam', 'Home']), None)
        c_away = next((c for c in cols if c in ['Away Team', 'AwayTeam', 'Away']), None)
        c_date = next((c for c in cols if c in ['Date', 'Scheduled', 'Datum']), None)
        c_res = next((c for c in cols if c in ['Result', 'Res', 'Výsledek']), None)

        if c_home and c_away:
            # 2. Filtrace pouze budoucích zápasů
            if c_res:
                # Označíme jako budoucí vše, kde není skóre (NaN, prázdno nebo pomlčka)
                mask_budouci = (
                    df_fixtures[c_res].isna() | 
                    (df_fixtures[c_res].astype(str).str.strip() == "") | 
                    (df_fixtures[c_res].astype(str).str.strip() == "-")
                )
                df_budouci = df_fixtures[mask_budouci].copy()
            else:
                df_budouci = df_fixtures.copy()

            if not df_budouci.empty:
                # 3. Přidání log (s ošetřením chyb v názvech)
                df_budouci[' '] = df_budouci[c_home].astype(str).str.strip().map(LOGA_TYMU)
                df_budouci['  '] = df_budouci[c_away].astype(str).str.strip().map(LOGA_TYMU)
                
                # 4. Výběr sloupců pro zobrazení
                vystupni_cols = []
                mapping_final = {}

                # Poskládáme tabulku podle toho, co máme k dispozici
                if c_date: 
                    vystupni_cols.append(c_date)
                    mapping_final[c_date] = 'Datum'
                
                vystupni_cols.extend([' ', c_home, c_away, '  '])
                mapping_final[c_home] = 'Domácí'
                mapping_final[c_away] = 'Hosté'

                df_final = df_budouci[vystupni_cols].rename(columns=mapping_final)

                st.dataframe(
                    df_final,
                    column_config={
                        " ": st.column_config.ImageColumn(" "),
                        "  ": st.column_config.ImageColumn(" ")
                    },
                    use_container_width=True,
                    hide_index=True
                )
                st.info(f"Aktuálně naplánováno {len(df_final)} zápasů.")
            else:
                st.info("Žádné nadcházející zápasy nebyly nalezeny.")
        else:
            st.error("V souboru chybí sloupce s týmy. Dostupné sloupce: " + str(cols))
    else:
        st.error("Data se nepodařilo stáhnout. Zkontrolujte připojení k FixtureDownload.com.")
        
