vimport pandas as pd
import streamlit as st
import requests
import io
import altair as alt
import math

# --- 1. POMOCNÉ FUNKCE A KONFIGURACE ---
st.set_page_config(page_title="PL Analytika 2026", layout="wide", page_icon="⚽")

def poisson_pmf(k, mu):
    if mu <= 0: 
        return 1.0 if k == 0 else 0.0
    try:
        return (math.exp(-mu) * (mu**k)) / math.factorial(k)
    except:
        return 0.0

LOGA_TYMU = {
    "Arsenal": "https://crests.football-data.org/57.png", "Aston Villa": "https://crests.football-data.org/58.png",
    "Bournemouth": "https://crests.football-data.org/1044.png", "Brentford": "https://crests.football-data.org/402.png",
    "Brighton": "https://crests.football-data.org/397.png", "Burnley": "https://crests.football-data.org/70.png",
    "Chelsea": "https://crests.football-data.org/61.png", "Crystal Palace": "https://crests.football-data.org/354.png",
    "Everton": "https://crests.football-data.org/62.png", "Fulham": "https://crests.football-data.org/63.png",
    "Leeds": "https://crests.football-data.org/341.png", "Liverpool": "https://crests.football-data.org/64.png",
    "Man City": "https://crests.football-data.org/65.png", "Man United": "https://crests.football-data.org/66.png",
    "Newcastle": "https://crests.football-data.org/67.png", "Nott'm Forest": "https://crests.football-data.org/351.png",
    "Southampton": "https://crests.football-data.org/340.png", "Sunderland": "https://crests.football-data.org/71.png",
    "Tottenham": "https://crests.football-data.org/73.png", "West Ham": "https://crests.football-data.org/563.png",
    "Wolves": "https://crests.football-data.org/76.png"
}

@st.cache_data(ttl=3600)
def nacti_data():
    try:
        df = pd.read_csv("https://www.football-data.co.uk/mmz4281/2526/E0.csv")
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
        return df
    except:
        return None

df_hist = nacti_data()
if df_hist is None:
    st.error("Nepodařilo se načíst data.")
    st.stop()

# --- WHO SCORED DATA ---
# Očekává se lokální soubor "whoscored.csv" se strukturou, kterou jsi poslal
df_ws = pd.read_csv("whoscored.csv")

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
    "Wolves": "Wolves"
}

# Převod názvů z WhoScored na názvy ve football-data
df_ws["TeamFD"] = df_ws["Team"].map(TEAM_NAME_MAP)

# Lookup slovník: klíč = název týmu ve football-data
WS_MAP = df_ws.set_index("TeamFD").to_dict(orient="index")

def get_ws_metrics(team_fd_name):
    """
    Vrátí metriky z WhoScored pro daný tým (ve jménu football-data),
    pokud nejsou, vrací nuly.
    """
    ws = WS_MAP.get(team_fd_name, None)
    if ws is None:
        return {
            "fouls": 0.0,
            "fouled": 0.0,
            "tackles": 0.0,
            "interceptions": 0.0,
            "shots": 0.0,
            "dribbles": 0.0
        }
    return {
        "fouls": ws.get("Fouls pg", 0.0),
        "fouled": ws.get("Fouled pg", 0.0),
        "tackles": ws.get("Tackles pg", 0.0),
        "interceptions": ws.get("Interceptions pg", 0.0),
        "shots": ws.get("Shots pg", 0.0),
        "dribbles": ws.get("Dribbles pg", 0.0)
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
    Vrátí predikci (pred_pro, pred_proti) pro daný tým a zvolenou metriku,
    s využitím kombinace: sezóna + forma + WhoScored.
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
            0.35 * avg_pro +
            0.25 * avg_last_5_pro +
            0.20 * ws_fouls +
            0.20 * ((ws_tackles + ws_inter) / 2)
        )
        pred_zk_proti = (
            0.35 * avg_proti +
            0.25 * avg_last_5_proti +
            0.20 * ws_fouled +
            0.20 * ((ws_tackles + ws_inter) / 2)
        )
        return pred_zk_pro, pred_zk_proti, avg_pro, avg_proti, avg_last_5_pro, avg_last_5_proti

    # --- ROHY ---
    if metrika_team == "Rohy":
        pred_rohy_pro = (
            0.35 * avg_pro +
            0.25 * avg_last_5_pro +
            0.20 * ws_shots +
            0.20 * ws_dribbles
        )
        pred_rohy_proti = (
            0.35 * avg_proti +
            0.25 * avg_last_5_proti +
            0.20 * ws_shots +
            0.20 * ws_dribbles
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

# --- GLOBÁLNÍ VÝPOČET TABULKY ---
týmy_seznam = sorted(df_hist['HomeTeam'].unique())
tabulka_vypocet = []
for t in týmy_seznam:
    d, v = df_hist[df_hist['HomeTeam'] == t], df_hist[df_hist['AwayTeam'] == t]
    b = (d['FTR']=='H').sum()*3 + (d['FTR']=='D').sum()*1 + (v['FTR']=='A').sum()*3 + (v['FTR']=='D').sum()*1
    sv, so = (d['FTHG'].sum() + v['FTAG'].sum()), (d['FTAG'].sum() + v['FTHG'].sum())
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
        # Získání všech zápasů týmu
        df_team = df_hist[(df_hist['HomeTeam'] == vybrany_team) | (df_hist['AwayTeam'] == vybrany_team)].copy()
        df_team['Date'] = pd.to_datetime(df_team['Date'], dayfirst=True)
        df_team = df_team.sort_values(by='Date', ascending=True)

        # Výpočet statistik pro každý zápas
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
        
        # Průměry sezóny
        avg_pro = df_stats['Pro'].mean()
        avg_proti = df_stats['Proti'].mean()

        # A) FORMA (5 zápasů, zleva nejnovější)
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

        # B) GRAF HISTORIE (Chronologicky, Dva sloupce)
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

        # C) PREDIKCE – NOVÝ KOMBINOVANÝ MODEL
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
    st.markdown("### Analýza rozhodčích PL 25/26")
    
    # Příprava seznamu rozhodčích
    original_refs = df_hist['Referee'].unique()
    ref_mapping = {}
    for r in original_refs:
        if isinstance(r, str) and " " in r:
            parts = r.split(" ")
            formatted = f"{parts[-1]} {' '.join(parts[:-1])}"
            ref_mapping[formatted] = r
        else:
            ref_mapping[r] = r
    
    seznam_ref_display = ["CELKEM"] + sorted(ref_mapping.keys())
    
    if 'ref_section_pick' not in st.session_state:
        st.session_state.ref_section_pick = "CELKEM"

    c_nav1, c_nav2 = st.columns([1, 1])
    
    with c_nav1:
        with st.popover(f"👮 Vyber rozhodčího: {st.session_state.ref_section_pick}", use_container_width=True):
            st.radio("Seznam:", seznam_ref_display, key="ref_section_pick")
    
    vybrany_zobrazeni = st.session_state.ref_section_pick

    with c_nav2:
        metrika_ref = st.radio("Metrika:", ["Fauly", "Žluté karty"], horizontal=True, label_visibility="collapsed")
    
    sloupce_metriky = ['HF', 'AF'] if metrika_ref == "Fauly" else ['HY', 'AY']
    label_metriky = "Počet faulů" if metrika_ref == "Fauly" else "Počet ŽK"

    # CELKEM
    if vybrany_zobrazeni == "CELKEM":
        stats_all = []
        for d_name, r_name in ref_mapping.items():
            df_r = df_hist[df_hist['Referee'] == r_name]
            if len(df_r) > 0:
                celkem_stat = df_r[sloupce_metriky].sum(axis=1).mean()
                stats_all.append({"Rozhodčí": d_name, "Průměr": round(celkem_stat, 2), "Zápasů": len(df_r)})
        
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
        ).encode(
            text='Průměr:Q'
        )
        
        st.altair_chart((bars + text).properties(height=600), use_container_width=True)

    # KONKRÉTNÍ ROZHODČÍ
    else:
        real_ref_name = ref_mapping[vybrany_zobrazeni]
        df_ref = df_hist[df_hist['Referee'] == real_ref_name].copy()
        
        df_ref = df_ref.sort_values(by='Date', ascending=True)
        
        df_ref['Hodnota'] = df_ref[sloupce_metriky].sum(axis=1)
        df_ref['Zapas_Nazev'] = df_ref['HomeTeam'] + " vs " + df_ref['AwayTeam']
        avg_season = df_ref['Hodnota'].mean()

        # FORMA (5)
        last_5 = df_ref.tail(5).sort_values(by='Date', ascending=False)
        forma_html = ""
        for _, row in last_5.iterrows():
            val = row['Hodnota']
            color = "#2ca02c" if val > avg_season else "#d62728"
            tooltip = f"{row['Date'].strftime('%d.%m.')}: {row['HomeTeam']} vs {row['AwayTeam']} ({int(val)})"
            forma_html += f'<div style="width: 20px; height: 20px; background-color: {color}; border-radius: 50%; margin: 0 5px;" title="{tooltip}"></div>'
        
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center;">
            <div style="font-size: 0.8rem; color: #555; margin-bottom: 8px; font-weight: bold;">FORMA (posledních 5 zápasů)</div>
            <div style="display: flex; justify-content: center; align-items: center;">{forma_html}</div>
            <div style="font-size: 0.7rem; color: #888; margin-top: 5px;">Průměr sezóny: {round(avg_season, 1)}</div>
        </div>
        """, unsafe_allow_html=True)

        # GRAF HISTORIE
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
        ).encode(
            text='Hodnota:Q'
        )
        
        st.altair_chart((bars_hist + text_hist).properties(height=max(300, len(df_ref) * 35)), use_container_width=True)

        # PREDIKCE
        avg_last_5 = last_5['Hodnota'].mean() if not last_5.empty else avg_season
        predikce_val = (avg_season + avg_last_5) / 2
        
        style_box = "background-color: #2b3035; padding: 20px; border-radius: 12px; color: white; text-align: center; margin-top: 20px;"
        
        st.markdown(f"""
        <div style="{style_box}">
            <div style="font-size: 0.9rem; color: #aaa; text-transform: uppercase; margin-bottom: 10px; letter-spacing: 1px;">
                🔮 Predikce pro další zápas ({metrika_ref})
            </div>
            <div style="display: flex; justify-content: space-around; align-items: center; border-top: 1px solid #444; padding-top: 15px;">
                <div>
                    <div style="font-size: 0.7rem; color: #888;">PRŮMĚR SEZÓNA</div>
                    <div style="font-size: 1.2rem; font-weight: bold; color: #ccc;">{round(avg_season, 1)}</div>
                </div>
                <div>
                    <div style="font-size: 0.7rem; color: #888;">FORMA (5)</div>
                    <div style="font-size: 1.2rem; font-weight: bold; color: #ccc;">{round(avg_last_5, 1)}</div>
                </div>
                <div>
                    <div style="font-size: 0.7rem; color: #4dabf7;">ODHAD MODELU</div>
                    <div style="font-size: 1.8rem; font-weight: bold; color: #fff;">{round(predikce_val, 1)}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- 6. SIMULÁTOR ZÁPASŮ ---
elif volba == "Simulátor zápasů":
    st.subheader("Analýza a predikce střetnutí")

    # Session state pro výběr týmů
    if 't1_pick' not in st.session_state: 
        st.session_state.t1_pick = týmy_seznam[0]
    if 't2_pick' not in st.session_state: 
        st.session_state.t2_pick = týmy_seznam[1]

    c1, c2, c3 = st.columns([1.5, 1.5, 1])
    with c1:
        st.selectbox("Domácí tým", týmy_seznam, key="t1_pick")
    with c2:
        st.selectbox("Hostující tým", týmy_seznam, key="t2_pick")
    with c3:
        metrika_sim = st.radio("Metrika", ["Fauly", "Žluté karty", "Rohy"])

    team_home = st.session_state.t1_pick
    team_away = st.session_state.t2_pick

    if team_home == team_away:
        st.warning("Vyber prosím dva různé týmy.")
    else:
        # Mapování sloupců stejné jako v Týmových statistikách
        map_metrics = {
            "Žluté karty": {"h": "HY", "a": "AY", "label": "Žluté karty"},
            "Fauly": {"h": "HF", "a": "AF", "label": "Fauly"},
            "Rohy": {"h": "HC", "a": "AC", "label": "Rohy"}
        }

        # Predikce pro jednotlivé týmy (samostatně)
        h_pred_pro, h_pred_proti, h_avg_pro, h_avg_proti, h_last5_pro, h_last5_proti = compute_predictions_for_team(
            team_home, metrika_sim, df_hist, map_metrics
        )
        a_pred_pro, a_pred_proti, a_avg_pro, a_avg_proti, a_last5_pro, a_last5_proti = compute_predictions_for_team(
            team_away, metrika_sim, df_hist, map_metrics
        )

        # Kombinace pro konkrétní zápas:
        # Domácí = průměr (jeho "pro" + soupeřovo "proti")
        # Hosté  = průměr (jejich "pro" + domácí "proti")
        home_expected = (h_pred_pro + a_pred_proti) / 2
        away_expected = (a_pred_pro + h_pred_proti) / 2

        # Zobrazení head-to-head boxu
        style_box_match = "background-color: #2b3035; padding: 20px; border-radius: 12px; color: white; margin-top: 10px;"

        col_h, col_mid, col_a = st.columns([3, 1, 3])
        with col_h:
            st.markdown(f"""
            <div style="{style_box_match}">
                <div style="font-size: 0.7rem; color: #aaa; text-transform: uppercase; margin-bottom: 6px;">DOMÁCÍ</div>
                <div style="font-size: 1.1rem; font-weight: bold; margin-bottom: 6px;">{team_home}</div>
                <div style="font-size: 0.8rem; color: #4dabf7; margin-bottom: 4px;">Očekávané {metrika_sim.lower()}</div>
                <div style="font-size: 2rem; font-weight: bold;">{round(home_expected, 1)}</div>
                <div style="font-size: 0.6rem; color: #aaa; margin-top: 8px;">
                    Sezóna: {round(h_avg_pro, 1)} | Forma 5: {round(h_last5_pro, 1)}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_mid:
            st.markdown("<div style='height:100%; display:flex; align-items:center; justify-content:center; font-size:1.2rem;'>vs</div>", unsafe_allow_html=True)
        with col_a:
            st.markdown(f"""
            <div style="{style_box_match}">
                <div style="font-size: 0.7rem; color: #aaa; text-transform: uppercase; margin-bottom: 6px; text-align:right;">HOSTÉ</div>
                <div style="font-size: 1.1rem; font-weight: bold; margin-bottom: 6px; text-align:right;'>{team_away}</div>
                <div style="font-size: 0.8rem; color: #ff6b6b; margin-bottom: 4px; text-align:right;">Očekávané {metrika_sim.lower()}</div>
                <div style="font-size: 2rem; font-weight: bold; text-align:right;'>{round(away_expected, 1)}</div>
                <div style="font-size: 0.6rem; color: #aaa; margin-top: 8px; text-align:right;">
                    Sezóna: {round(a_avg_pro, 1)} | Forma 5: {round(a_last5_pro, 1)}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Malý souhrnný text
        st.markdown(
            f"<div style='margin-top:15px; font-size:0.85rem; color:#888;'>"
            f"Model kombinuje sezónní průměry, formu posledních 5 zápasů a WhoScored statistiky "
            f"(fauly, obranné zákroky, střely, dribbles) pro odhad {metrika_sim.lower()} v konkrétním zápase."
            f"</div>",
            unsafe_allow_html=True
        )
