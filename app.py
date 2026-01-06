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
import scipy.stats as stats  # Budeme potřebovat pro Poissonovu distribuci

elif volba == "Simulátor zápasů":
    st.header("Analýza a predikce střetnutí")
    týmy = sorted(df_hist['HomeTeam'].unique())
    
    # 1. Výběr domácího týmu
    t1 = st.selectbox("Domácí tým (výběr):", týmy, index=0)
    
    # 2. LOGA V JEDNOM ŘÁDKU (HTML/Flexbox)
    t2_val = st.session_state.get('t2_select', týmy[1])
    logo1, logo2 = LOGA_TYMU.get(t1, ""), LOGA_TYMU.get(t2_val, "")

    html_kód = f"""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0;">
        <div style="text-align: center; width: 30%;">
            <img src="{logo1}" width="80"><br>
            <span style="color: gray; font-size: 0.8rem; font-weight: bold;">{t1.upper()}</span>
        </div>
        <div style="text-align: center; width: 40%;">
            <h1 style="margin: 0; font-size: 2.5rem; color: #555;">VS</h1>
        </div>
        <div style="text-align: center; width: 30%;">
            <img src="{logo2}" width="80"><br>
            <span style="color: gray; font-size: 0.8rem; font-weight: bold;">{t2_val.upper()}</span>
        </div>
    </div>
    """
    st.markdown(html_kód, unsafe_allow_html=True)
        
    # 3. Výběr hostujícího týmu
    t2 = st.selectbox("Hostující tým (výběr):", týmy, index=1, key='t2_select')
    
    st.write("---")
    
    # --- VÝPOČTY STATISTIK ---
    def get_stats(team):
        d = df_hist[df_hist['HomeTeam'] == team]
        v = df_hist[df_hist['AwayTeam'] == team]
        z = len(d) + len(v)
        if z == 0: return {"G_vstr":0, "G_ink":0, "Rohy":0, "Karty":0, "Fauly":0}
        return {
            "G_vstr": (d['FTHG'].sum() + v['FTAG'].sum()) / z,
            "G_ink": (d['FTAG'].sum() + v['FTHG'].sum()) / z,
            "Rohy": (d['HC'].sum() + v['AC'].sum()) / z,
            "Karty": (d['HY'].sum() + v['AY'].sum()) / z,
            "Fauly": (d['HF'].sum() + v['AF'].sum()) / z
        }
    
    s1, s2 = get_stats(t1), get_stats(t2)
    
    # Průměrné očekávané góly
    mu_domaci = (s1["G_vstr"] + s2["G_ink"]) / 2
    mu_hoste = (s2["G_vstr"] + s1["G_ink"]) / 2
    
    # --- POISSONŮV VÝPOČET PRAVDĚPODOBNOSTÍ ---
    prob_domaci, prob_hoste, prob_remiza = 0, 0, 0
    # Simulujeme výsledky až do 10:10 gólů
    for i in range(11):
        for j in range(11):
            p = stats.poisson.pmf(i, mu_domaci) * stats.poisson.pmf(j, mu_hoste)
            if i > j: prob_domaci += p
            elif i < j: prob_hoste += p
            else: prob_remiza += p

    # --- ZOBRAZENÍ PREDIKCE ---
    st.subheader("🎯 Predikce a pravděpodobnosti")
    
    # Metriky očekávaného skóre
    p1, p2, p3 = st.columns(3)
    p1.metric(f"Očekávané góly {t1}", round(mu_domaci, 2))
    p2.metric("Předpokládané skóre", f"{round(mu_domaci)} : {round(mu_hoste)}")
    p3.metric(f"Očekávané góly {t2}", round(mu_hoste, 2))
    
    # Procentuální šance (1-X-2)
    st.write("")
    c1, c2, c3 = st.columns(3)
    c1.info(f"**Výhra {t1}** \n{round(prob_domaci * 100, 1)} %")
    c2.info(f"**Remíza** \n{round(prob_remiza * 100, 1)} %")
    c3.info(f"**Výhra {t2}** \n{round(prob_hoste * 100, 1)} %")
    
    st.write("---")
    
    # --- TABULKA SROVNÁNÍ ---
    res_df = pd.DataFrame({
        "Metrika": ["Góly vstřelené", "Góly inkasované", "Rohy", "Fauly", "Žluté karty"],
        t1: [round(s1["G_vstr"], 2), round(s1["G_ink"], 2), round(s1["Rohy"], 2), round(s1["Fauly"], 2), round(s1["Karty"], 2)],
        t2: [round(s2["G_vstr"], 2), round(s2["G_ink"], 2), round(s2["Rohy"], 2), round(s2["Fauly"], 2), round(s2["Karty"], 2)]
    })
    st.table(res_df)
    
