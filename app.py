import pandas as pd
import streamlit as st
import requests
import io
import altair as alt
import scipy.stats as stats

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
        df = pd.read_csv("https://www.football-data.co.uk/mmz4281/2526/E0.csv")
        return df
    except:
        return None

df_hist = nacti_data()

st.sidebar.title("⚽ SPORT-MATH")
volba = st.sidebar.radio("Sekce:", ["Tabulka PL", "Týmové statistiky", "Rozhodčí", "Simulátor zápasů"])

if df_hist is None:
    st.error("Chyba: Nepodařilo se načíst data.")
    st.stop()

# --- POMOCNÉ FUNKCE ---
def ziskej_formu(team, df):
    zápasy = df[(df['HomeTeam'] == team) | (df['AwayTeam'] == team)].tail(5)
    forma = []
    for _, row in zápasy.iterrows():
        if row['FTR'] == 'D': forma.append("🟡")
        elif (row['HomeTeam'] == team and row['FTR'] == 'H') or (row['AwayTeam'] == team and row['FTR'] == 'A'):
            forma.append("🟢")
        else: forma.append("🔴")
    return "".join(forma)

# --- 1. TABULKA ---
if volba == "Tabulka PL":
    st.header("Aktuální pořadí Premier League 25/26")
    týmy = sorted(df_hist['HomeTeam'].unique())
    tabulka_data = []
    for t in týmy:
        d = df_hist[df_hist['HomeTeam'] == t]
        v = df_hist[df_hist['AwayTeam'] == t]
        b = (d['FTR']=='H').sum()*3 + (d['FTR']=='D').sum()*1 + (v['FTR']=='A').sum()*3 + (v['FTR']=='D').sum()*1
        sv, so = (d['FTHG'].sum() + v['FTAG'].sum()), (d['FTAG'].sum() + v['FTHG'].sum())
        tabulka_data.append({"Tým": t, "Z": len(d)+len(v), "Skóre": f"{int(sv)}:{int(so)}", "GD": sv-so, "B": b, "Forma": ziskej_formu(t, df_hist)})
    
    df_res = pd.DataFrame(tabulka_data).sort_values(by=["B", "GD"], ascending=False).reset_index(drop=True)
    df_res.index += 1
    df_res.insert(0, ' ', df_res['Tým'].map(LOGA_TYMU))
    st.dataframe(df_res, column_config={" ": st.column_config.ImageColumn(" ")}, use_container_width=True, hide_index=True)

# --- 2. STATISTIKY ---
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
    base = alt.Chart(df_p).encode(y=alt.Y('Tým:N', sort=sort_order, title=None), x=alt.X('Hodnota:Q', stack='normalize', axis=None),
        color=alt.Color('Typ:N', scale=alt.Scale(domain=['Udělané', 'Obdržené'], range=['#2ca02c', '#d62728']), legend=alt.Legend(orient="top", title=None)))
    bars = base.mark_bar()
    txt_ud = alt.Chart(df_p[df_p['Typ'] == 'Udělané']).mark_text(align='left', dx=10, color='white', fontWeight='bold').encode(y=alt.Y('Tým:N', sort=sort_order), x=alt.value(0), text='Hodnota:Q')
    txt_ob = alt.Chart(df_p[df_p['Typ'] == 'Obdržené']).mark_text(align='right', dx=-10, color='white', fontWeight='bold').encode(y=alt.Y('Tým:N', sort=sort_order), x=alt.X('sum(Hodnota):Q', stack='normalize'), text='Hodnota:Q')
    st.altair_chart((bars + txt_ud + txt_ob).properties(height=700), use_container_width=True)


# --- 3. ROZHODČÍ (NOVÁ SEKCE) ---
elif volba == "Rozhodčí":
    st.header("Analýza rozhodčích Premier League 25/26")
    
    if 'Referee' in df_hist.columns:
        ref_stats = []
        rozhodci_list = df_hist['Referee'].unique()
        
        for r in rozhodci_list:
            zapas_ref = df_hist[df_hist['Referee'] == r]
            pocet_zapasu = len(zapas_ref)
            if pocet_zapasu > 0:
                zlute = zapas_ref['HY'].sum() + zapas_ref['AY'].sum()
                cervene = zapas_ref['HR'].sum() + zapas_ref['AR'].sum()
                fauly = zapas_ref['HF'].sum() + zapas_ref['AF'].sum()
                
                ref_stats.append({
                    "Rozhodčí": r,
                    "Zápasy": pocet_zapasu,
                    "Fauly/zápas": round(fauly / pocet_zapasu, 2),
                    "ŽK/zápas": round(zlute / pocet_zapasu, 2),
                    "ČK celkem": int(cervene)
                })
        
        df_ref = pd.DataFrame(ref_stats).sort_values(by="ŽK/zápas", ascending=False).reset_index(drop=True)
        df_ref.index += 1
        
        # Zobrazení tabulky
        st.dataframe(df_ref, use_container_width=True)
        
        # Graf nejpřísnějších rozhodčích (podle ŽK)
        st.subheader("Průměr žlutých karet na zápas")
        chart_ref = alt.Chart(df_ref.head(10)).mark_bar(color='#ff4b4b').encode(
            x=alt.X('ŽK/zápas:Q', title="Průměr žlutých karet"),
            y=alt.Y('Rozhodčí:N', sort='-x', title=None)
        ).properties(height=400)
        
        st.altair_chart(chart_ref, use_container_width=True)
        
        st.info("Tip: Sledujte rozhodčí s průměrem nad 4.5 ŽK/zápas, tam bývá prostor pro sázky na karty.")
    else:
        st.warning("Data o rozhodčích nejsou v tomto souboru k dispozici.")


# --- 4. SIMULÁTOR ---
# --- 4. SIMULÁTOR ZÁPASŮ (KOMPLETNÍ) ---
elif volba == "Simulátor zápasů":
    st.header("Analýza a predikce střetnutí")
    týmy = sorted(df_hist['HomeTeam'].unique())
    
    # 1. Výběry
    t1 = st.selectbox("Domácí tým (výběr):", týmy, index=0)
    t2_val = st.session_state.get('t2_select', týmy[1])
    
    # HTML Loga
    logo1, logo2 = LOGA_TYMU.get(t1, ""), LOGA_TYMU.get(t2_val, "")
    html_kód = f"""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0;">
        <div style="text-align: center; width: 30%;"><img src="{logo1}" width="80"><br><span style="color: gray; font-size: 0.8rem; font-weight: bold;">{t1.upper()}</span></div>
        <div style="text-align: center; width: 40%;"><h1 style="margin: 0; font-size: 2.5rem; color: #555;">VS</h1></div>
        <div style="text-align: center; width: 30%;"><img src="{logo2}" width="80"><br><span style="color: gray; font-size: 0.8rem; font-weight: bold;">{t2_val.upper()}</span></div>
    </div>
    """
    st.markdown(html_kód, unsafe_allow_html=True)
    
    t2 = st.selectbox("Hostující tým (výběr):", týmy, index=1, key='t2_select')
    
    # Výběr rozhodčího
    ref_list = sorted(df_hist['Referee'].unique()) if 'Referee' in df_hist.columns else []
    vybrany_ref = st.selectbox("Rozhodčí zápasu:", ref_list)
    
    st.write("---")
    
    # --- VÝPOČTY STATISTIK ---
    def get_stats(team):
        d, v = df_hist[df_hist['HomeTeam'] == team], df_hist[df_hist['AwayTeam'] == team]
        z = len(d) + len(v)
        if z == 0: return {"G_v":0, "G_i":0, "R":0, "K":0, "F":0}
        return {
            "G_v": (d['FTHG'].sum() + v['FTAG'].sum())/z, 
            "G_i": (d['FTAG'].sum() + v['FTHG'].sum())/z, 
            "R": (d['HC'].sum() + v['AC'].sum())/z, 
            "K": (d['HY'].sum() + v['AY'].sum())/z, 
            "F": (d['HF'].sum() + v['AF'].sum())/z
        }

    s1, s2 = get_stats(t1), get_stats(t2)
    
    # Průměry pro Poisson
    mu_d = (s1["G_v"] + s2["G_i"]) / 2
    mu_h = (s2["G_v"] + s1["G_i"]) / 2
    
    # Statistiky rozhodčího
    ref_df = df_hist[df_hist['Referee'] == vybrany_ref]
    ref_zk_avg = (ref_df['HY'].sum() + ref_df['AY'].sum()) / len(ref_df) if len(ref_df) > 0 else 0
    ocekavane_karty = (s1["K"] + s2["K"] + ref_zk_avg) / 1.5

    # --- ZOBRAZENÍ 1: PREDIKCE SKÓRE A KARET ---
    st.subheader("🎯 Predikce zápasu")
    p1, p2, p3 = st.columns(3)
    p1.metric(f"Góly {t1}", round(mu_d, 2))
    p2.metric("Předpokládané skóre", f"{round(mu_d)} : {round(mu_h)}")
    p3.metric(f"Góly {t2}", round(mu_h, 2))
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Očekávané ŽK", round(ocekavane_karty, 1))
    k2.metric("Průměr rozhodčího", f"{round(ref_zk_avg, 1)} ŽK")
    k3.write("") # prázdné pro zarovnání

    # Poissonův výpočet pravděpodobností (1-X-2)
    p_d, p_h, p_r = 0, 0, 0
    for i in range(11):
        for j in range(11):
            p = poisson_pmf(i, mu_d) * poisson_pmf(j, mu_h)
            if i > j: p_d += p
            elif i < j: p_h += p
            else: p_r += p

    st.write("")
    o1, o2, o3 = st.columns(3)
    o1.success(f"**Výhra {t1}**\n{round(p_d * 100, 1)} %")
    o2.warning(f"**Remíza**\n{round(p_r * 100, 1)} %")
    o3.error(f"**Výhra {t2}**\n{round(p_h * 100, 1)} %")

    if ocekavane_karty > 4.5:
        st.error(f"🔥 **Vysoký potenciál karet!**")
    
    st.write("---")
    
    # --- ZOBRAZENÍ 2: SROVNÁVACÍ TABULKA A FORMA ---
    st.subheader("📊 Srovnání průměrů a Forma")
    st.write(f"**Forma {t1}:** {ziskej_formu(t1, df_hist)} | **Forma {t2}:** {ziskej_formu(t2, df_hist)}")
    
    res_df = pd.DataFrame({
        "Metrika": ["Góly vstřelené", "Góly inkasované", "Rohy", "Fauly", "Žluté karty"],
        t1: [round(s1["G_v"], 2), round(s1["G_i"], 2), round(s1["R"], 2), round(s1["F"], 2), round(s1["K"], 2)],
        t2: [round(s2["G_v"], 2), round(s2["G_i"], 2), round(s2["R"], 2), round(s2["F"], 2), round(s2["K"], 2)]
    })
    st.table(res_df)
    
