import pandas as pd
import streamlit as st
import requests
import io
import altair as alt
import math

# --- 1. POMOCNÉ FUNKCE A KONFIGURACE ---
st.set_page_config(page_title="PL Analytika 2026", layout="wide", page_icon="⚽")

# --- VÝBĚR LIGY MUSÍ BÝT NAHOŘE ---
liga = st.sidebar.selectbox(
    "Liga:",
    ["Premier League", "La Liga", "Serie A"]
)

def poisson_pmf(k, mu):
    if mu <= 0:
        return 1.0 if k == 0 else 0.0
    try:
        return (math.exp(-mu) * (mu**k)) / math.factorial(k)
    except:
        return 0.0

LOGA_TYMU = {
    # --- Premier League ---
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
    "Newcastle": "https://crests.football-data.org/67.png",
    "Nott'm Forest": "https://crests.football-data.org/351.png",
    "Southampton": "https://crests.football-data.org/340.png",
    "Sunderland": "https://crests.football-data.org/71.png",
    "Tottenham": "https://crests.football-data.org/73.png",
    "West Ham": "https://crests.football-data.org/563.png",
    "Wolves": "https://crests.football-data.org/76.png",

    # --- La Liga ---
    "Real Madrid": "https://crests.football-data.org/86.png",
    "Barcelona": "https://crests.football-data.org/81.png",
    "Atletico Madrid": "https://crests.football-data.org/78.png",
    "Girona": "https://crests.football-data.org/298.png",
    "Ath Bilbao": "https://crests.football-data.org/77.png",
    "Real Sociedad": "https://crests.football-data.org/92.png",
    "Betis": "https://crests.football-data.org/90.png",
    "Valencia": "https://crests.football-data.org/95.png",
    "Villarreal": "https://crests.football-data.org/94.png",
    "Osasuna": "https://crests.football-data.org/79.png",
    "Sevilla": "https://crests.football-data.org/559.png",
    "Rayo Vallecano": "https://crests.football-data.org/87.png",
    "Getafe": "https://crests.football-data.org/82.png",
    "Celta": "https://crests.football-data.org/558.png",
    "Mallorca": "https://crests.football-data.org/89.png",
    "Alaves": "https://crests.football-data.org/263.png",
    "Las Palmas": "https://crests.football-data.org/275.png",
    "Leganes": "https://crests.football-data.org/745.png",
    "Espanyol": "https://crests.football-data.org/80.png",
    "Valladolid": "https://crests.football-data.org/250.png",

    # --- Serie A ---
    "Inter": "https://crests.football-data.org/108.png",
    "AC Milan": "https://crests.football-data.org/98.png",
    "Juventus": "https://crests.football-data.org/109.png",
    "Napoli": "https://crests.football-data.org/113.png",
    "Atalanta": "https://crests.football-data.org/102.png",
    "Roma": "https://crests.football-data.org/100.png",
    "Lazio": "https://crests.football-data.org/110.png",
    "Fiorentina": "https://crests.football-data.org/99.png",
    "Bologna": "https://crests.football-data.org/103.png",
    "Torino": "https://crests.football-data.org/586.png",
    "Monza": "https://crests.football-data.org/591.png",
    "Genoa": "https://crests.football-data.org/107.png",
    "Udinese": "https://crests.football-data.org/115.png",
    "Sassuolo": "https://crests.football-data.org/471.png",
    "Cagliari": "https://crests.football-data.org/104.png",
    "Empoli": "https://crests.football-data.org/445.png",
    "Verona": "https://crests.football-data.org/450.png",
    "Lecce": "https://crests.football-data.org/867.png",
    "Parma": "https://crests.football-data.org/112.png",
    "Venezia": "https://crests.football-data.org/1104.png"
}

@st.cache_data(ttl=3600)
def nacti_data(liga):
    url_map = {
        "Premier League": "https://www.football-data.co.uk/mmz4281/2526/E0.csv",
        "La Liga": "https://www.football-data.co.uk/mmz4281/2526/SP1.csv",
        "Serie A": "https://www.football-data.co.uk/mmz4281/2526/I1.csv"
    }
    try:
        df = pd.read_csv(url_map[liga])
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
        return df
    except:
        return None

df_hist = nacti_data(liga)
if df_hist is None:
    st.error("Nepodařilo se načíst data.")
    st.stop()


# Mapování názvů týmů mezi WhoScored a football-data
TEAM_NAME_MAP = {
    "Arsenal": "Arsenal",
    "Aston Villa": "Aston Villa",
    "Bournemouth": "Bournemouth",
    "Brentford": "Brentford",
    "Brighton": "Brighton",
    "Burnley": "Burnley",
    "Chelsea": "Chelsea",
    "Crystal Palace": "Crystal Palace",
    "Everton": "Everton",
    "Fulham": "Fulham",
    "Leeds": "Leeds",
    "Liverpool": "Liverpool",
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Newcastle": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "Sunderland": "Sunderland",
    "Tottenham": "Tottenham",
    "West Ham": "West Ham",
    "Wolves": "Wolves",
    # La Liga
    "Real Madrid": "Real Madrid",
    "Barcelona": "Barcelona",
    "Atlético Madrid": "Atletico Madrid",
    "Girona": "Girona",
    "Athletic Club": "Ath Bilbao",
    "Real Sociedad": "Real Sociedad",
    "Real Betis": "Betis",
    "Valencia": "Valencia",
    "Villarreal": "Villarreal",
    "Osasuna": "Osasuna",
    "Sevilla": "Sevilla",
    "Rayo Vallecano": "Rayo Vallecano",
    "Getafe": "Getafe",
    "Celta Vigo": "Celta",
    "Mallorca": "Mallorca",
    "Alavés": "Alaves",
    "Las Palmas": "Las Palmas",
    "Leganés": "Leganes",
    "Espanyol": "Espanyol",
    "Valladolid": "Valladolid",

    # Serie A
    "Inter": "Inter",
    "AC Milan": "AC Milan",
    "Juventus": "Juventus",
    "Napoli": "Napoli",
    "Atalanta": "Atalanta",
    "Roma": "Roma",
    "Lazio": "Lazio",
    "Fiorentina": "Fiorentina",
    "Bologna": "Bologna",
    "Torino": "Torino",
    "Monza": "Monza",
    "Genoa": "Genoa",
    "Udinese": "Udinese",
    "Sassuolo": "Sassuolo",
    "Cagliari": "Cagliari",
    "Empoli": "Empoli",
    "Verona": "Verona",
    "Lecce": "Lecce",
    "Parma": "Parma",
    "Venezia": "Venezia"
}

# --- WHO SCORED DATA ---
ws_map = {
    "Premier League": "whoscored.csv",
    "La Liga": None,
    "Serie A": None
}

# WhoScored data používáme pouze pro Premier League
if liga == "Premier League":
    df_ws = pd.read_csv(ws_map[liga], encoding="utf-8")
    df_ws.columns = df_ws.columns.str.strip()
    df_ws["TeamFD"] = df_ws["Team"].map(TEAM_NAME_MAP)
    WS_MAP = df_ws.set_index("TeamFD").to_dict(orient="index")
else:
    df_ws = None
    WS_MAP = {}


def get_ws_metrics(team_fd_name):
    """
    Vrátí metriky z WhoScored pro daný tým (ve jménu football-data),
    pokud nejsou dostupné (La Liga, Serie A), vrací nuly.
    """

    # Pokud nejsou WhoScored data (La Liga, Serie A)
    if WS_MAP == {}:
        return {
            "fouls": 0.0,
            "fouled": 0.0,
            "tackles": 0.0,
            "interceptions": 0.0,
            "shots": 0.0,
            "dribbles": 0.0,
            "xg": 0.0,
            "goals": 0.0
        }

    ws = WS_MAP.get(team_fd_name)
    if ws is None:
        return {
            "fouls": 0.0,
            "fouled": 0.0,
            "tackles": 0.0,
            "interceptions": 0.0,
            "shots": 0.0,
            "dribbles": 0.0,
            "xg": 0.0,
            "goals": 0.0
        }

    return {
        "fouls": ws.get("Fouls pg", 0.0),
        "fouled": ws.get("Fouled pg", 0.0),
        "tackles": ws.get("Tackles pg", 0.0),
        "interceptions": ws.get("Interceptions pg", 0.0),
        "shots": ws.get("Shots pg", 0.0),
        "dribbles": ws.get("Dribbles pg", 0.0),
        "xg": ws.get("xG", 0.0),
        "goals": ws.get("Goals", 0.0)
    }

def compute_team_history_stats(df_hist, team, cols):
    """
    Vrátí (avg_pro, avg_proti, last5_pro, last5_proti) pro daný tým a zvolené sloupce.
    cols: dict {'h': 'HF'/'HY'/'HC', 'a': 'AF'/'AY'/'AC'}
    """
    df_team = df_hist[(df_hist['HomeTeam'] == team) | (df_hist['AwayTeam'] == team)].copy()
    if df_team.empty:
        return 0.0, 0.0, 0.0, 0.0

    df_team['Date'] = pd.to_datetime(df_team['Date'], dayfirst=True)
    df_team = df_team.sort_values(by='Date', ascending=True)

    stats_rows = []
    for _, row in df_team.iterrows():
        if row['HomeTeam'] == team:
            val_pro = row[cols['h']]
            val_proti = row[cols['a']]
        else:
            val_pro = row[cols['a']]
            val_proti = row[cols['h']]
        stats_rows.append({
            "Datum": row['Date'],
            "Pro": val_pro,
            "Proti": val_proti
        })
    df_stats = pd.DataFrame(stats_rows)

    avg_pro = df_stats['Pro'].mean()
    avg_proti = df_stats['Proti'].mean()

    last_5 = df_stats.tail(5)
    avg_last_5_pro = last_5['Pro'].mean() if not last_5.empty else avg_pro
    avg_last_5_proti = last_5['Proti'].mean() if not last_5.empty else avg_proti

    return avg_pro, avg_proti, avg_last_5_pro, avg_last_5_proti

def compute_predictions_for_team(team, metrika_team, df_hist, map_metrics):
    """
    Vrátí predikci (pred_pro, pred_proti, avg_pro, avg_proti, avg_last_5_pro, avg_last_5_proti)
    pro daný tým a zvolenou metriku, s využitím kombinace: sezóna + forma + WhoScored.
    """
    cols = map_metrics[metrika_team]

    # Historie z football-data
    avg_pro, avg_proti, avg_last_5_pro, avg_last_5_proti = compute_team_history_stats(df_hist, team, cols)

    # WhoScored metriky
    ws = get_ws_metrics(team)
    ws_fouls = ws["fouls"]
    ws_fouled = ws["fouled"]
    ws_tackles = ws["tackles"]
    ws_inter = ws["interceptions"]
    ws_shots = ws["shots"]
    ws_dribbles = ws["dribbles"]

    # --- FAULY ---
    if metrika_team == "Fauly":
        pred_fauly_pro = (
            0.40 * avg_pro +
            0.30 * avg_last_5_pro +
            0.30 * ws_fouls
        )
        pred_fauly_proti = (
            0.40 * avg_proti +
            0.30 * avg_last_5_proti +
            0.30 * ws_fouled
        )
        return pred_fauly_pro, pred_fauly_proti, avg_pro, avg_proti, avg_last_5_pro, avg_last_5_proti

    # --- ŽLUTÉ KARTY ---
    if metrika_team == "Žluté karty":
        pred_zk_pro = (
            0.45 * avg_pro +
            0.35 * avg_last_5_pro +
            0.10 * ws_fouls +
            0.10 * ((ws_tackles + ws_inter) / 2)
        )
        pred_zk_proti = (
            0.45 * avg_proti +
            0.35 * avg_last_5_proti +
            0.10 * ws_fouled +
            0.10 * ((ws_tackles + ws_inter) / 2)
        )
        return pred_zk_pro, pred_zk_proti, avg_pro, avg_proti, avg_last_5_pro, avg_last_5_proti

    # --- ROHY ---
    if metrika_team == "Rohy":
        pred_rohy_pro = (
            0.50 * avg_pro +
            0.30 * avg_last_5_pro +
            0.10 * ws_shots +
            0.10 * ws_dribbles
        )
        pred_rohy_proti = (
            0.50 * avg_proti +
            0.30 * avg_last_5_proti +
            0.10 * ws_shots +
            0.10 * ws_dribbles
        )
        return pred_rohy_pro, pred_rohy_proti, avg_pro, avg_proti, avg_last_5_pro, avg_last_5_proti

    # Fallback
    pred_pro = (avg_pro + avg_last_5_pro) / 2
    pred_proti = (avg_proti + avg_last_5_proti) / 2
    return pred_pro, pred_proti, avg_pro, avg_proti, avg_last_5_pro, avg_last_5_proti

def ziskej_formu(team, df):
    zápasy = df[(df['HomeTeam'] == team) | (df['AwayTeam'] == team)].sort_values(by='Date').tail(5)
    forma = []
    for _, row in zápasy.iterrows():
        if row['FTR'] == 'D':
            forma.append("🟡")
        elif (row['HomeTeam'] == team and row['FTR'] == 'H') or (row['AwayTeam'] == team and row['FTR'] == 'A'):
            forma.append("🟢")
        else:
            forma.append("🔴")
    return "".join(forma)

# --- GLOBÁLNÍ VÝPOČET TABULKY + SÍLA TÝMŮ ---
týmy_seznam = sorted(df_hist['HomeTeam'].unique())
tabulka_vypocet = []
for t in týmy_seznam:
    d = df_hist[df_hist['HomeTeam'] == t]
    v = df_hist[df_hist['AwayTeam'] == t]
    b = (d['FTR']=='H').sum()*3 + (d['FTR']=='D').sum()*1 + (v['FTR']=='A').sum()*3 + (v['FTR']=='D').sum()*1
    sv = d['FTHG'].sum() + v['FTAG'].sum()
    so = d['FTAG'].sum() + v['FTHG'].sum()
    tabulka_vypocet.append({"Tým": t, "B": b, "GD": sv-so})

df_top = pd.DataFrame(tabulka_vypocet).sort_values(by=["B", "GD"], ascending=False).reset_index(drop=True)
df_top.index += 1

def urci_silu(tym):
    try:
        pozice = df_top[df_top['Tým'] == tym].index[0]
        if pozice <= 6:
            return 'A'
        elif pozice >= 15:
            return 'C'
        else:
            return 'B'
    except:
        return 'B'


# --- 2. NAVIGACE ---
st.sidebar.title("⚽ SPORT-MATH")

volba = st.sidebar.radio("Sekce:", ["Tabulka PL", "Týmové statistiky", "Rozhodčí", "Simulátor zápasů"])

# --- 3. SEKCE: TABULKA PL ---
if volba == "Tabulka PL":
    st.subheader("Aktuální pořadí Premier League 25/26")
    tabulka_final = []
    for t in týmy_seznam:
        d, v = df_hist[df_hist['HomeTeam'] == t], df_hist[df_hist['AwayTeam'] == t]
        b = (d['FTR']=='H').sum()*3 + (d['FTR']=='D').sum()*1 + (v['FTR']=='A').sum()*3 + (v['FTR']=='D').sum()*1
        sv, so = (d['FTHG'].sum() + v['FTAG'].sum()), (d['FTAG'].sum() + v['FTHG'].sum())
        forma_str = ziskej_formu(t, df_hist)[::-1]
        tabulka_final.append({
            "Tým": t,
            "Z": len(d)+len(v),
            "Skóre": f"{int(sv)}:{int(so)}",
            "GD": sv-so,
            "B": b,
            "Forma": forma_str
        })
    
    df_res = pd.DataFrame(tabulka_final).sort_values(by=["B", "GD"], ascending=False).reset_index(drop=True)
    df_res.index += 1
    df_res.insert(0, ' ', df_res['Tým'].map(LOGA_TYMU))

    def styluj_tabulku(x):
        df_s = pd.DataFrame('', index=x.index, columns=x.columns)
        if len(x) >= 4: 
            df_s.iloc[0:4, :] = 'background-color: rgba(30, 144, 255, 0.1)'
        if len(x) >= 17: 
            df_s.iloc[-3:, :] = 'background-color: rgba(255, 69, 0, 0.1)'
        return df_s

    st.dataframe(
        df_res.style.apply(styluj_tabulku, axis=None),
        column_config={" ": st.column_config.ImageColumn(" ")},
        use_container_width=True
    )

# --- 4. TÝMOVÉ STATISTIKY ---
elif volba == "Týmové statistiky":
    st.markdown("### Detailní týmové statistiky")

    # UI Ovládání (Popover + Radio)
    if 'team_stats_pick' not in st.session_state:
        st.session_state.team_stats_pick = "CELKEM"

    c_nav1, c_nav2 = st.columns([1, 1])
    
    with c_nav1:
        team_list = ["CELKEM"] + sorted(týmy_seznam)
        with st.popover(f"👕 Vyber tým: {st.session_state.team_stats_pick}", use_container_width=True):
            st.radio("Seznam:", team_list, key="team_stats_pick")
    
    vybrany_team = st.session_state.team_stats_pick

    with c_nav2:
        metrika_team = st.radio("Metrika:", ["Fauly", "Žluté karty", "Rohy"], horizontal=True, label_visibility="collapsed")

    # Mapování sloupců
    map_metrics = {
        "Žluté karty": {"h": "HY", "a": "AY", "label": "Žluté karty"},
        "Fauly": {"h": "HF", "a": "AF", "label": "Fauly"},
        "Rohy": {"h": "HC", "a": "AC", "label": "Rohy"}
    }
    cols = map_metrics[metrika_team]

    # --- LOGIKA: CELKEM (PŘEHLED VŠECH TÝMŮ) ---
    if vybrany_team == "CELKEM":
        data_all = []
        for t in týmy_seznam:
            mask_h = df_hist['HomeTeam'] == t
            mask_a = df_hist['AwayTeam'] == t
            
            zapasu = mask_h.sum() + mask_a.sum()
            if zapasu > 0:
                pro = (df_hist[mask_h][cols['h']].sum() + df_hist[mask_a][cols['a']].sum()) / zapasu
                proti = (df_hist[mask_h][cols['a']].sum() + df_hist[mask_a][cols['h']].sum()) / zapasu
                
                data_all.append({"Tým": t, "Typ": "Pro (Udělané)", "Hodnota": round(pro, 1)})
                data_all.append({"Tým": t, "Typ": "Proti (Obdržené)", "Hodnota": round(proti, 1)})

        df_chart = pd.DataFrame(data_all)
        
        base = alt.Chart(df_chart).encode(
            y=alt.Y('Tým:N', title=None),
            x=alt.X('Hodnota:Q', title=f'Průměr {metrika_team} na zápas'),
            color=alt.Color(
                'Typ:N', 
                scale=alt.Scale(
                    domain=['Pro (Udělané)', 'Proti (Obdržené)'], 
                    range=['#4dabf7', '#ff6b6b']
                ),
                legend=alt.Legend(title="Legenda", orient="top")
            )
        )

        bars = base.mark_bar().encode(
            yOffset='Typ:N'
        )

        text = base.mark_text(
            align='left',
            baseline='middle',
            dx=3
        ).encode(
            yOffset='Typ:N',
            text='Hodnota:Q'
        )

        st.altair_chart((bars + text).properties(height=800), use_container_width=True)

    # --- LOGIKA: KONKRÉTNÍ TÝM ---
    else:
        df_team = df_hist[(df_hist['HomeTeam'] == vybrany_team) | (df_hist['AwayTeam'] == vybrany_team)].copy()
        df_team['Date'] = pd.to_datetime(df_team['Date'], dayfirst=True)
        df_team = df_team.sort_values(by='Date', ascending=True)

        stats_rows = []
        for _, row in df_team.iterrows():
            if row['HomeTeam'] == vybrany_team:
                val_pro = row[cols['h']]
                val_proti = row[cols['a']]
                souper = row['AwayTeam']
                kde = "(D)"
            else:
                val_pro = row[cols['a']]
                val_proti = row[cols['h']]
                souper = row['HomeTeam']
                kde = "(V)"
            
            stats_rows.append({
                "Datum": row['Date'],
                "Zápas": f"{kde} vs {souper}",
                "Pro": val_pro,
                "Proti": val_proti
            })
        
        df_stats = pd.DataFrame(stats_rows)
        
        avg_pro = df_stats['Pro'].mean()
        avg_proti = df_stats['Proti'].mean()

        # FORMA (5 zápasů)
        last_5 = df_stats.tail(5).sort_values(by='Datum', ascending=False)
        forma_html = ""
        for _, row in last_5.iterrows():
            val = row['Pro']
            color = "#2ca02c" if val > avg_pro else "#d62728"
            tooltip = f"{row['Zápas']}: {int(val)} (Průměr: {round(avg_pro, 1)})"
            forma_html += f'<div style="width: 20px; height: 20px; background-color: {color}; border-radius: 50%; margin: 0 5px;" title="{tooltip}"></div>'

        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center;">
            <div style="font-size: 0.8rem; color: #555; margin-bottom: 8px; font-weight: bold;">FORMA (posledních 5 zápasů - zleva nejnovější)</div>
            <div style="display: flex; justify-content: center; align-items: center;">{forma_html}</div>
            <div style="font-size: 0.7rem; color: #888; margin-top: 5px;">Zelená = Nad průměrem ({round(avg_pro, 1)}) | Červená = Pod průměrem</div>
        </div>
        """, unsafe_allow_html=True)

        # GRAF HISTORIE
        df_long = df_stats.melt(
            id_vars=['Zápas', 'Datum'], 
            value_vars=['Pro', 'Proti'], 
            var_name='Typ', 
            value_name='Hodnota'
        )
        
        base_hist = alt.Chart(df_long).encode(
            y=alt.Y('Zápas:N', sort=None, title="Zápas (chronologicky)"),
            x=alt.X('Hodnota:Q', title=metrika_team),
            color=alt.Color(
                'Typ:N', 
                scale=alt.Scale(domain=['Pro', 'Proti'], range=['#4dabf7', '#ff6b6b']),
                legend=alt.Legend(orient="top", title=None)
            )
        )
        
        bars_hist = base_hist.mark_bar().encode(
            yOffset='Typ:N'
        )
        
        text_hist = base_hist.mark_text(
            align='left',
            baseline='middle',
            dx=3,
            color='white'
        ).encode(
            yOffset='Typ:N',
            text='Hodnota:Q'
        )
        
        st.altair_chart((bars_hist + text_hist).properties(height=max(350, len(df_stats) * 40)), use_container_width=True)

        # --- PREDIKCE – NOVÝ KOMBINOVANÝ MODEL ---
        pred_pro, pred_proti, avg_pro_all, avg_proti_all, avg_last_5_pro, avg_last_5_proti = compute_predictions_for_team(
            vybrany_team, metrika_team, df_hist, map_metrics
        )

        style_box = "background-color: #2b3035; padding: 20px; border-radius: 12px; color: white; text-align: center; margin-top: 20px;"

        st.markdown(f"""
        <div style="{style_box}">
            <div style="font-size: 0.9rem; color: #aaa; text-transform: uppercase; margin-bottom: 10px; letter-spacing: 1px;">
                🔮 Predikce pro další zápas
            </div>
            <div style="display: flex; justify-content: space-around; align-items: center; border-top: 1px solid #444; padding-top: 15px;">
                <div style="text-align: center;">
                    <div style="font-size: 0.7rem; color: #4dabf7; margin-bottom: 5px;">OČEKÁVANÉ {metrika_team.upper()}</div>
                    <div style="font-size: 1.8rem; font-weight: bold; color: #fff;">{round(pred_pro, 1)}</div>
                    <div style="font-size: 0.6rem; color: #888;">(Sezóna: {round(avg_pro_all, 1)} | Forma 5: {round(avg_last_5_pro, 1)})</div>
                </div>
                <div style="border-left: 1px solid #555; height: 40px;"></div>
                <div style="text-align: center;">
                    <div style="font-size: 0.7rem; color: #ff6b6b; margin-bottom: 5px;">OČEKÁVANÉ OD SOUPEŘE</div>
                    <div style="font-size: 1.8rem; font-weight: bold; color: #fff;">{round(pred_proti, 1)}</div>
                    <div style="font-size: 0.6rem; color: #888;">(Sezóna: {round(avg_proti_all, 1)} | Forma 5: {round(avg_last_5_proti, 1)})</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# --- 5. ROZHODČÍ ---
elif volba == "Rozhodčí":

    st.markdown(f"### Analýza rozhodčích – {liga}")

    # --- 1) NAČTENÍ DAT PODLE LIGY ---
    if liga == "Premier League":
        df_refs = df_hist.copy()

    elif liga == "La Liga":
        df_refs = pd.read_csv("SP1.csv")   # máš doplněný sloupec Referee

    elif liga == "Serie A":
        df_refs = pd.read_csv("I1.csv")    # máš doplněný sloupec Referee

    else:
        st.info("Pro tuto ligu nejsou dostupná data o rozhodčích.")
        st.stop()

    df_refs.columns = df_refs.columns.str.strip()

    # Parsování datumu
    if "Date" in df_refs.columns:
        df_refs["Date"] = pd.to_datetime(df_refs["Date"], errors="coerce")

    # Kontrola sloupce
    if "Referee" not in df_refs.columns:
        st.warning("Dataset neobsahuje sloupec 'Referee'.")
        st.stop()

    if df_refs["Referee"].dropna().empty:
        st.warning("V datasetu nejsou dostupná data o rozhodčích.")
        st.stop()

    # --- 2) PŘÍPRAVA SEZNAMU ROZHODČÍCH ---
    original_refs = df_refs["Referee"].dropna().unique()

    ref_mapping = {}
    for r in original_refs:
        if isinstance(r, str) and " " in r:
            parts = r.split(" ")
            formatted = f"{parts[-1]} {' '.join(parts[:-1])}"
            ref_mapping[formatted] = r
        else:
            ref_mapping[r] = r

    seznam_ref_display = ["CELKEM"] + sorted(ref_mapping.keys())

    # Session state
    if 'ref_section_pick' not in st.session_state:
        st.session_state.ref_section_pick = "CELKEM"

    c_nav1, c_nav2 = st.columns([1, 1])

    with c_nav1:
        with st.popover(f"👮 Vyber rozhodčího: {st.session_state.ref_section_pick}", use_container_width=True):
            st.radio("Seznam:", seznam_ref_display, key="ref_section_pick")

    vybrany_zobrazeni = st.session_state.ref_section_pick

    with c_nav2:
        metrika_ref = st.radio("Metrika:", ["Fauly", "Žluté karty"], horizontal=True, label_visibility="collapsed")

    # Mapování metriky
    sloupce_metriky = ['HF', 'AF'] if metrika_ref == "Fauly" else ['HY', 'AY']
    label_metriky = "Počet faulů" if metrika_ref == "Fauly" else "Počet ŽK"

    # Kontrola sloupců
    for col in sloupce_metriky:
        if col not in df_refs.columns:
            st.warning(f"Dataset neobsahuje sloupec '{col}'.")
            st.stop()

    # --- 3) CELKOVÝ PŘEHLED ---
    if vybrany_zobrazeni == "CELKEM":

        stats_all = []
        for d_name, r_name in ref_mapping.items():
            df_r = df_refs[df_refs['Referee'] == r_name]
            if len(df_r) > 0:
                celkem_stat = df_r[sloupce_metriky].sum(axis=1).mean()
                stats_all.append({
                    "Rozhodčí": d_name,
                    "Průměr": round(celkem_stat, 2),
                    "Zápasů": len(df_r)
                })

        if not stats_all:
            st.info("Pro tuto ligu nejsou dostupné statistiky rozhodčích.")
            st.stop()

        df_chart = pd.DataFrame(stats_all).sort_values("Průměr", ascending=False)

        base = alt.Chart(df_chart).encode(
            x=alt.X('Průměr:Q', title=f'Průměr {metrika_ref} na zápas'),
            y=alt.Y('Rozhodčí:N', sort='-x'),
            tooltip=['Rozhodčí', 'Průměr', 'Zápasů']
        )

        bars = base.mark_bar().encode(
            color=alt.Color('Průměr:Q', scale=alt.Scale(scheme='blues'), legend=None)
        )

        text = base.mark_text(
            align='left',
            baseline='middle',
            dx=3
        ).encode(text='Průměr:Q')

        st.altair_chart((bars + text).properties(height=600), use_container_width=True)

    # --- 4) DETAIL KONKRÉTNÍHO ROZHODČÍHO ---
    else:
        real_ref_name = ref_mapping[vybrany_zobrazeni]
        df_ref = df_refs[df_refs['Referee'] == real_ref_name].copy()

        if df_ref.empty:
            st.info("Tento rozhodčí nemá v této sezóně žádné zápasy.")
            st.stop()

        df_ref = df_ref.sort_values(by='Date', ascending=True)

        df_ref['Hodnota'] = df_ref[sloupce_metriky].sum(axis=1)
        df_ref['Zapas_Nazev'] = df_ref['HomeTeam'] + " vs " + df_ref['AwayTeam']
        avg_season = df_ref['Hodnota'].mean()

        # --- FORMA (5 zápasů) ---
        last_5 = df_ref.tail(5).sort_values(by='Date', ascending=False)
        forma_html = ""
        for _, row in last_5.iterrows():
            val = row['Hodnota']
            color = "#2ca02c" if val > avg_season else "#d62728"
            tooltip = f"{row['Date'].strftime('%d.%m.')}: {row['HomeTeam']} vs {row['AwayTeam']} ({int(val)})"
            forma_html += (
                f'<div style="width: 20px; height: 20px; background-color: {color}; '
                f'border-radius: 50%; margin: 0 5px;" title="{tooltip}"></div>'
            )

        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; 
                    margin-bottom: 20px; text-align: center;">
            <div style="font-size: 0.8rem; color: #555; margin-bottom: 8px; font-weight: bold;">
                FORMA (posledních 5 zápasů)
            </div>
            <div style="display: flex; justify-content: center; align-items: center;">
                {forma_html}
            </div>
            <div style="font-size: 0.7rem; color: #888; margin-top: 5px;">
                Průměr sezóny: {round(avg_season, 1)}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- GRAF HISTORIE ---
        df_ref['Datum_Str'] = df_ref['Date'].dt.strftime('%d.%m.%Y')

        base_hist = alt.Chart(df_ref).encode(
            y=alt.Y('Zapas_Nazev:N', sort=None, title="Zápas (chronologicky)"),
            x=alt.X('Hodnota:Q', title=label_metriky),
            tooltip=['Datum_Str', 'Zapas_Nazev', 'Hodnota']
        )

        bars_hist = base_hist.mark_bar().encode(
            color=alt.condition(
                alt.datum.Hodnota > avg_season,
                alt.value('#1f77b4'),
                alt.value('#aec7e8')
            )
        )

        text_hist = base_hist.mark_text(
            align='left',
            baseline='middle',
            dx=3,
            color='white'
        ).encode(text='Hodnota:Q')

        st.altair_chart((bars_hist + text_hist).properties(
            height=max(300, len(df_ref) * 35)
        ), use_container_width=True)

        # --- PREDIKCE ---
        avg_last_5 = last_5['Hodnota'].mean() if not last_5.empty else avg_season
        predikce_val = (avg_season + avg_last_5) / 2

        style_box = (
            "background-color: #2b3035; padding: 20px; border-radius: 12px; "
            "color: white; text-align: center; margin-top: 20px;"
        )

        st.markdown(f"""
        <div style="{style_box}">
            <div style="font-size: 0.9rem; color: #aaa; text-transform: uppercase; 
                        margin-bottom: 10px; letter-spacing: 1px;">
                🔮 Predikce pro další zápas ({metrika_ref})
            </div>
            <div style="display: flex; justify-content: space-around; align-items: center; 
                        border-top: 1px solid #444; padding-top: 15px;">
                <div>
                    <div style="font-size: 0.7rem; color: #888;">PRŮMĚR SEZÓNA</div>
                    <div style="font-size: 1.2rem; font-weight: bold; color: #ccc;">
                        {round(avg_season, 1)}
                    </div>
                </div>
                <div>
                    <div style="font-size: 0.7rem; color: #888;">FORMA (5)</div>
                    <div style="font-size: 1.2rem; font-weight: bold; color: #ccc;">
                        {round(avg_last_5, 1)}
                    </div>
                </div>
                <div>
                    <div style="font-size: 0.7rem; color: #4dabf7;">ODHAD MODELU</div>
                    <div style="font-size: 1.8rem; font-weight: bold; color: #fff;">
                        {round(predikce_val, 1)}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)



# --- 6. SIMULÁTOR ZÁPASŮ ---
elif volba == "Simulátor zápasů":

    # --- NAČTENÍ DAT PRO ROZHODČÍ / LIGOVÉ STATISTIKY ---
    if liga == "Premier League":
        df_refs_sim = df_hist.copy()
    elif liga == "La Liga":
        df_refs_sim = pd.read_csv("SP1.csv")
    elif liga == "Serie A":
        df_refs_sim = pd.read_csv("I1.csv")
    else:
        df_refs_sim = df_hist.copy()  # fallback pro jistotu

    df_refs_sim.columns = df_refs_sim.columns.str.strip()

    if "Date" in df_refs_sim.columns:
        df_refs_sim["Date"] = pd.to_datetime(df_refs_sim["Date"], errors="coerce")

    # --- KONTROLA ROZHODČÍCH ---
    has_referees = ("Referee" in df_refs_sim.columns) and df_refs_sim["Referee"].notna().any()

    vybrany_ref = None
    ref_faktor = 1.0
    ref_zk_factor = 1.0

    if has_referees:
        original_refs = df_refs_sim["Referee"].dropna().unique()

        # mapování jmen: "Anthony Taylor" → "Taylor Anthony"
        ref_mapping = {}
        for r in original_refs:
            if isinstance(r, str) and " " in r:
                parts = r.split(" ")
                formatted = f"{parts[-1]} {' '.join(parts[:-1])}"
                ref_mapping[formatted] = r
            else:
                ref_mapping[r] = r

        ref_display_list = sorted(ref_mapping.keys())

        if ref_display_list:
            if 'ref_display_pick' not in st.session_state:
                st.session_state.ref_display_pick = ref_display_list[0]

            with st.popover(f"🏁 Rozhodčí: {st.session_state.ref_display_pick}", use_container_width=True):
                st.radio("Vyber rozhodčího:", ref_display_list, key="ref_display_pick")

            vybrany_ref = ref_mapping.get(st.session_state.ref_display_pick)

    # pokud není vybraný rozhodčí, použijeme ligový průměr
    if has_referees and vybrany_ref is not None:
        ref_data = df_refs_sim[df_refs_sim['Referee'] == vybrany_ref]
    else:
        ref_data = df_refs_sim



    # --- FUNKCE: VÝPOČET DLE SÍLY SOUPEŘE PRO GÓLY ---
    def ziskej_stats_sila(tym, role, sila_soupere, sloupec):
        if role == 'Home':
            z = df_hist[df_hist['HomeTeam'] == tym].copy()
            z['Sila_Soupere'] = z['AwayTeam'].apply(urci_silu)
        else:
            z = df_hist[df_hist['AwayTeam'] == tym].copy()
            z['Sila_Soupere'] = z['HomeTeam'].apply(urci_silu)
        
        res = z[z['Sila_Soupere'] == sila_soupere][sloupec]
        if not res.empty:
            return res.mean()
        return df_hist[df_hist[role + 'Team'] == tym][sloupec].mean()

    # --- 1. GÓLY (xG) – HYBRIDNÍ MODEL ---
    sila_t1, sila_t2 = urci_silu(t1), urci_silu(t2)

    mu_d_raw = (ziskej_stats_sila(t1, 'Home', sila_t2, 'FTHG') +
                ziskej_stats_sila(t2, 'Away', sila_t1, 'FTHG')) / 2
    mu_h_raw = (ziskej_stats_sila(t2, 'Away', sila_t1, 'FTAG') +
                ziskej_stats_sila(t1, 'Home', sila_t2, 'FTAG')) / 2

    ws_t1 = get_ws_metrics(t1)
    ws_t2 = get_ws_metrics(t2)

    faktor_t1 = (ws_t1["xg"] / ws_t1["goals"]) if ws_t1["goals"] > 0 else 1.0
    faktor_t2 = (ws_t2["xg"] / ws_t2["goals"]) if ws_t2["goals"] > 0 else 1.0

    mu_d = mu_d_raw * faktor_t1
    mu_h = mu_h_raw * faktor_t2

    celkem_goly = mu_d + mu_h

    # --- 2. FAULY / ROHY / KARTY ---
    map_metrics_sim = {
        "Žluté karty": {"h": "HY", "a": "AY"},
        "Fauly": {"h": "HF", "a": "AF"},
        "Rohy": {"h": "HC", "a": "AC"}
    }

    # FAULY
    h_fauly_pro, _, _, _, _, _ = compute_predictions_for_team(t1, "Fauly", df_hist, map_metrics_sim)
    a_fauly_pro, _, _, _, _, _ = compute_predictions_for_team(t2, "Fauly", df_hist, map_metrics_sim)

    ligovy_avg_f = (df_refs_sim['HF'] + df_refs_sim['AF']).mean()

    if has_referees and vybrany_ref is not None:
        ref_data = df_refs_sim[df_refs_sim['Referee'] == vybrany_ref]
    else:
        ref_data = df_refs_sim

    ref_avg_f = ref_data[['HF', 'AF']].sum(axis=1).mean() if not ref_data.empty else ligovy_avg_f
    ref_faktor = ref_avg_f / ligovy_avg_f if ligovy_avg_f > 0 else 1.0

    ocek_fauly = (h_fauly_pro + a_fauly_pro) * ref_faktor

    # ROHY
    h_rohy_pro, _, _, _, _, _ = compute_predictions_for_team(t1, "Rohy", df_hist, map_metrics_sim)
    a_rohy_pro, _, _, _, _, _ = compute_predictions_for_team(t2, "Rohy", df_hist, map_metrics_sim)

    ocek_rohy = h_rohy_pro + a_rohy_pro

       # KARTY
    h_zk_pro, _, _, _, _, _ = compute_predictions_for_team(t1, "Žluté karty", df_hist, map_metrics_sim)
    a_zk_pro, _, _, _, _, _ = compute_predictions_for_team(t2, "Žluté karty", df_hist, map_metrics_sim)

    ligovy_avg_zk = (df_refs_sim['HY'] + df_refs_sim['AY']).mean()

    # --- LIGA-SPECIFICKÝ KOREKČNÍ FAKTOR PRO KARTY ---
    liga_karty_multiplier = 1.0
    if liga == "La Liga":
        liga_karty_multiplier = 2.20   # kalibrace na 4.22 ŽK + podhodnocený model
    elif liga == "Serie A":
        liga_karty_multiplier = 1.23   # kalibrace na 3.76 ŽK

    ref_zk_avg = ref_data[['HY', 'AY']].sum(axis=1).mean() if not ref_data.empty else ligovy_avg_zk

    base_karty = (h_zk_pro + a_zk_pro) / 2 if (h_zk_pro + a_zk_pro) > 0 else ligovy_avg_zk
    ref_zk_factor = ref_zk_avg / ligovy_avg_zk if ligovy_avg_zk > 0 else 1.0

    ocek_karty = base_karty * ref_zk_factor * liga_karty_multiplier

    # --- 3. POISSON ---
    p_1, p_x, p_2 = 0, 0, 0
    for i in range(10):
        for j in range(10):
            p = poisson_pmf(i, mu_d) * poisson_pmf(j, mu_h)
            if i > j:
                p_1 += p
            elif i < j:
                p_2 += p
            else:
                p_x += p

    p1_pct = round(p_1 * 100)
    px_pct = round(p_x * 100)
    p2_pct = 100 - p1_pct - px_pct

    prob_over_2_5 = sum(
        poisson_pmf(i, mu_d) * poisson_pmf(j, mu_h)
        for i in range(10) for j in range(10) if i + j > 2
    )

    # --- VIZUALIZACE ZÁPASU (LOGA + VS) ---
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0;">
        <div style="text-align: center; width: 30%;">
            <img src="{LOGA_TYMU.get(t1)}" width="80"><br>
            <span style="color: gray; font-size: 0.8rem; font-weight: bold;">{t1.upper()}</span>
        </div>
        <div style="text-align: center; width: 40%;">
            <h1 style="margin: 0; font-size: 2.5rem; color: #555;">VS</h1>
        </div>
        <div style="text-align: center; width: 30%;">
            <img src="{LOGA_TYMU.get(t2)}" width="100"><br>
            <span style="color: gray; font-size: 0.8rem; font-weight: bold;">{t2.upper()}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


    # --- FORMA ---
    f1 = ziskej_formu(t1, df_hist)[::-1]
    f2 = ziskej_formu(t2, df_hist)[::-1]
    
    forma_html = f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <div style="font-size: 0.85rem; font-weight: bold; color: #666; margin-bottom: 5px;">AKTUÁLNÍ FORMA</div>
        <div style="display: flex; justify-content: center; gap: 30px; font-size: 1.1rem; letter-spacing: 2px;">
            <div>{f1}</div>
            <div style="color: #ccc; font-size: 0.8rem; font-weight: bold; display: flex; align-items: center;">VS</div>
            <div>{f2}</div>
        </div>
    </div>
    """
    st.markdown(forma_html, unsafe_allow_html=True)

    # --- BOXY ---
    style_box = "background-color: #2b3035; padding: 15px; border-radius: 12px; color: white; margin-bottom: 5px; text-align: center;"

    st.markdown(f"""
    <div style="{style_box} border-bottom: 1px solid #444; border-bottom-left-radius: 0; border-bottom-right-radius: 0;">
        <div style="display: flex; justify-content: space-around; align-items: center;">
            <div>
                <div style="font-size: 0.7rem; color: #aaa; text-transform: uppercase;">xG Domácí</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #4dabf7;">{round(mu_d, 2)}</div>
            </div>
            <div>
                <div style="font-size: 0.7rem; color: #aaa; text-transform: uppercase;">Predikce skóre</div>
                <div style="font-size: 2rem; font-weight: bold;">{round(mu_d)} : {round(mu_h)}</div>
            </div>
            <div>
                <div style="font-size: 0.7rem; color: #aaa; text-transform: uppercase;">xG Hosté</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #ff6b6b;">{round(mu_h, 2)}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="{style_box} border-top-left-radius: 0; border-top-right-radius: 0; padding-top: 10px;">
        <div style="display: flex; justify-content: space-around; align-items: center;">
            <div>
                <div style="font-size: 0.7rem; color: #aaa; text-transform: uppercase;">🚩 Rohy</div>
                <div style="font-size: 1.2rem; font-weight: bold;">{round(ocek_rohy, 1)}</div>
            </div>
            <div>
                <div style="font-size: 0.7rem; color: #aaa; text-transform: uppercase;">⚖️ Fauly</div>
                <div style="font-size: 1.2rem; font-weight: bold;">{round(ocek_fauly, 1)}</div>
            </div>
            <div>
                <div style="font-size: 0.7rem; color: #aaa; text-transform: uppercase;">🟨 Karty</div>
                <div style="font-size: 1.2rem; font-weight: bold;">{round(ocek_karty, 1)}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- VIZUÁLNÍ PRUH ---
    st.markdown(f"""
    <div style="margin-top: -5px; margin-bottom: 25px;">
        <div style="display: flex; width: 100%; height: 10px; border-radius: 5px; overflow: hidden; border: 1px solid #444;">
            <div style="width: {p1_pct}%; background-color: #4dabf7;"></div>
            <div style="width: {px_pct}%; background-color: #666;"></div>
            <div style="width: {p2_pct}%; background-color: #ff6b6b;"></div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: #aaa; padding-top: 5px; font-weight: bold;">
            <span>{t1}: {p1_pct}%</span>
            <span>REMÍZA: {px_pct}%</span>
            <span>{t2}: {p2_pct}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- TIPY ---
    st.subheader("💡 Doporučené tipy")
    tipy = []
    if celkem_goly > 3.0:
        tipy.append("🔥 **Góly:** Over 2.5")
    if ocek_rohy > 11.0:
        tipy.append("🚩 **Rohy:** Over 10.5")
    if ocek_fauly > 24:
        tipy.append(f"⚠️ **Fauly:** Over 23.5 (Ref faktor: {round(ref_faktor, 2)})")
    if ocek_karty > 4.5:
        tipy.append("🟨 **Karty:** Over 3.5")
    
    for t in tipy:
        st.info(t)

    # --- VALUE BETS ---
    st.write("---")
    st.subheader("💰 Vyhledávač Value Bets")
    st.caption("Porovnej kurzy sázkové kanceláře s matematickým modelem")

    c_odds1, c_odds2, c_odds3 = st.columns(3)
    odd_1 = c_odds1.number_input(f"Kurz na {t1}", min_value=1.01, value=2.00, step=0.05)
    odd_x = c_odds2.number_input("Kurz na Remízu", min_value=1.01, value=3.20, step=0.05)
    odd_2 = c_odds3.number_input(f"Kurz na {t2}", min_value=1.01, value=3.50, step=0.05)
    
    odd_over = st.number_input("Kurz na Over 2.5 gólu", min_value=1.01, value=1.85, step=0.05)

    if st.button("Analyzovat výhodnost kurzů", use_container_width=True):
        def check_value(prob, odd, label):
            value = (prob * odd) - 1
            fair_kurz = 1/prob if prob > 0 else 0
            if value > 0.05:
                st.success(f"✅ **{label}**: Hodnota {round(value*100, 1)}% (Fair kurz: {round(fair_kurz, 2)})")
            elif value < -0.15:
                st.error(f"❌ **{label}**: Nevýhodné (Fair kurz: {round(fair_kurz, 2)})")
            else:
                st.warning(f"⚖️ **{label}**: Bez výrazné hodnoty (Fair kurz: {round(fair_kurz, 2)})")

        check_value(p_1, odd_1, f"Výhra {t1}")
        check_value

