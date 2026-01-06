import pandas as pd
import streamlit as st
import requests
import io
import altair as alt

# --- KONFIGURACE A LOGA ---
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

@st.cache_data(ttl=3600)
def nacti_data():
    try:
        # Používáme pouze jeden, stabilní zdroj
        df = pd.read_csv("https://www.football-data.co.uk/mmz4281/2526/E0.csv")
        return df
    except:
        return None

df_hist = nacti_data()

# --- NAVIGACE ---
st.sidebar.title("⚽ SPORT-MATH")
volba = st.sidebar.radio("Sekce:", ["Tabulka PL", "Týmové statistiky", "Simulátor zápasů"])

if df_hist is None:
    st.error("Chyba: Nepodařilo se připojit k datovému serveru.")
    st.stop()

# --- 1. TABULKA (Body + GD + Řazení) ---
if volba == "Tabulka PL":
    st.header("Aktuální pořadí Premier League 25/26")
    týmy = sorted(df_hist['HomeTeam'].unique())
    data = []
    for t in týmy:
        d = df_hist[df_hist['HomeTeam'] == t]
        v = df_hist[df_hist['AwayTeam'] == t]
        b = (d['FTR']=='H').sum()*3 + (d['FTR']=='D').sum()*1 + (v['FTR']=='A').sum()*3 + (v['FTR']=='D').sum()*1
        sv = d['FTHG'].sum() + v['FTAG'].sum()
        so = d['FTAG'].sum() + v['FTHG'].sum()
        data.append({"Tým": t, "Z": len(d)+len(v), "Skóre": f"{int(sv)}:{int(so)}", "GD": sv-so, "B": b})
    
    df_res = pd.DataFrame(data).sort_values(by=["B", "GD"], ascending=False).reset_index(drop=True)
    df_res.index += 1
    df_res.insert(0, ' ', df_res['Tým'].map(LOGA_TYMU))
    st.dataframe(df_res, column_config={" ": st.column_config.ImageColumn(" ")}, use_container_width=True, hide_index=True)

# --- 2. STATISTIKY (Fixnuté grafy s bílými čísly u krajů) ---
elif volba == "Týmové statistiky":
    metrika = st.radio("Metrika:", ["Žluté karty", "Fauly", "Rohy"], horizontal=True)
    m = {"Žluté karty": ("HY", "AY"), "Fauly": ("HF", "AF"), "Rohy": ("HC", "AC")}[metrika]
    
    plot_data = []
    for t in sorted(df_hist['HomeTeam'].unique()):
        mask_h, mask_a = df_hist['HomeTeam']==t, df_hist['AwayTeam']==t
        z = len(df_hist[mask_h | mask_a])
        ud = (df_hist[mask_h][m[0]].sum() + df_hist[mask_a][m[1]].sum()) / z
        ob = (df_hist[mask_h][m[1]].sum() + df_hist[mask_a][m[0]].sum()) / z
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
    txt_ud = alt.Chart(df_p[df_p['Typ'] == 'Udělané']).mark_text(align='left', dx=10, color='white', fontWeight='bold').encode(y=alt.Y('Tým:N', sort=sort_order), x=alt.value(0), text='Hodnota:Q')
    txt_ob = alt.Chart(df_p[df_p['Typ'] == 'Obdržené']).mark_text(align='right', dx=-10, color='white', fontWeight='bold').encode(y=alt.Y('Tým:N', sort=sort_order), x=alt.X('sum(Hodnota):Q', stack='normalize'), text='Hodnota:Q')

    st.altair_chart((bars + txt_ud + txt_ob).properties(height=700), use_container_width=True)

# --- 3. SIMULÁTOR ZÁPASŮ (Místo nespolehlivých příštích zápasů) ---
elif volba == "Simulátor zápasů":
    st.header("Analýza konkrétního střetnutí")
    týmy = sorted(df_hist['HomeTeam'].unique())
    
    col1, col2 = st.columns(2)
    t1 = col1.selectbox("Domácí tým", týmy, index=0)
    t2 = col2.selectbox("Hostující tým", týmy, index=1)
    
    col1.image(LOGA_TYMU.get(t1, ""), width=100)
    col2.image(LOGA_TYMU.get(t2, ""), width=100)
    
    st.write("---")
    st.subheader("Rychlé srovnání (Průměry)")
    
    # Funkce pro výpočet průměrů týmu
    def get_stats(team):
        d = df_hist[df_hist['HomeTeam'] == team]
        v = df_hist[df_hist['AwayTeam'] == team]
        z = len(d) + len(v)
        return {
            "Góly": (d['FTHG'].sum() + v['FTAG'].sum()) / z,
            "Inkasované": (d['FTAG'].sum() + v['FTHG'].sum()) / z,
            "Rohy": (d['HC'].sum() + v['AC'].sum()) / z,
            "Karty": (d['HY'].sum() + v['AY'].sum()) / z
        }
    
    s1, s2 = get_stats(t1), get_stats(t2)
    
    res_df = pd.DataFrame({
        "Metrika": ["Vstřelené góly", "Inkasované góly", "Rohové kopy", "Žluté karty"],
        t1: [round(s1["Góly"], 2), round(s1["Inkasované"], 2), round(s1["Rohy"], 2), round(s1["Karty"], 2)],
        t2: [round(s2["Góly"], 2), round(s2["Inkasované"], 2), round(s2["Rohy"], 2), round(s2["Karty"], 2)]
    })
    
    st.table(res_df)
