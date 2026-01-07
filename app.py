import pandas as pd
import streamlit as st
import requests
import io
import altair as alt
import math

# --- 1. POMOCNÉ FUNKCE A KONFIGURACE ---
st.set_page_config(page_title="PL Analytika 2026", layout="wide", page_icon="⚽")

def poisson_pmf(k, mu):
    """Ruční výpočet Poissonova rozdělení"""
    if mu <= 0: return 1.0 if k == 0 else 0.0
    try:
        return (math.exp(-mu) * (mu**k)) / math.factorial(k)
    except:
        return 0.0

# AKTUALIZOVANÁ LOGA (Leeds, Sunderland, Burnley jsou zpět)
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
    "Newcastle": "https://crests.football-data.org/67.png",
    "Nott'm Forest": "https://crests.football-data.org/351.png",
    "Southampton": "https://crests.football-data.org/340.png",
    "Sunderland": "https://crests.football-data.org/71.png",
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

def ziskej_formu(team, df):
    zápasy = df[(df['HomeTeam'] == team) | (df['AwayTeam'] == team)].tail(5)
    forma = []
    for _, row in zápasy.iterrows():
        if row['FTR'] == 'D': forma.append("🟡")
        elif (row['HomeTeam'] == team and row['FTR'] == 'H') or (row['AwayTeam'] == team and row['FTR'] == 'A'):
            forma.append("🟢")
        else: forma.append("🔴")
    return "".join(forma)

df_hist = nacti_data()

# --- 2. NAVIGACE ---
st.sidebar.title("⚽ SPORT-MATH")
volba = st.sidebar.radio("Sekce:", ["Tabulka PL", "Týmové statistiky", "Rozhodčí", "Simulátor zápasů"])

if df_hist is None:
    st.error("Nepodařilo se načíst data.")
    st.stop()

# --- 3. SEKCE: TABULKA PL (OPRAVENÁ FORMA ZLEVA) ---
if volba == "Tabulka PL":
    st.header("Aktuální pořadí Premier League 25/26")
    týmy = sorted(df_hist['HomeTeam'].unique())
    tabulka_data = []
    
    for t in týmy:
        d, v = df_hist[df_hist['HomeTeam'] == t], df_hist[df_hist['AwayTeam'] == t]
        b = (d['FTR']=='H').sum()*3 + (d['FTR']=='D').sum()*1 + (v['FTR']=='A').sum()*3 + (v['FTR']=='D').sum()*1
        sv, so = (d['FTHG'].sum() + v['FTAG'].sum()), (d['FTAG'].sum() + v['FTHG'].sum())
        
        # ZDE JE ZMĚNA: Přidáno [[::-1]] pro otočení formy (nejnovější zápas vlevo)
        forma_str = ziskej_formu(t, df_hist)[::-1]
        
        tabulka_data.append({
            "Tým": t, 
            "Z": len(d)+len(v), 
            "Skóre": f"{int(sv)}:{int(so)}", 
            "GD": sv-so, 
            "B": b, 
            "Forma": forma_str
        })
    
    df_res = pd.DataFrame(tabulka_data).sort_values(by=["B", "GD"], ascending=False).reset_index(drop=True)
    df_res.index += 1
    df_res.insert(0, ' ', df_res['Tým'].map(LOGA_TYMU))
    
    # Zobrazení tabulky
    st.dataframe(
        df_res, 
        column_config={" ": st.column_config.ImageColumn(" ")}, 
        use_container_width=True, 
        hide_index=False
    )
    


# --- 4. SEKCE: TÝMOVÉ STATISTIKY ---
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
    base = alt.Chart(df_p).encode(y=alt.Y('Tým:N', sort=sort_order, title=None), x=alt.X('Hodnota:Q', stack='normalize', axis=None), color=alt.Color('Typ:N', scale=alt.Scale(domain=['Udělané', 'Obdržené'], range=['#2ca02c', '#d62728']), legend=alt.Legend(orient="top", title=None)))
    bars = base.mark_bar()
    txt_ud = alt.Chart(df_p[df_p['Typ'] == 'Udělané']).mark_text(align='left', dx=10, color='white', fontWeight='bold').encode(y=alt.Y('Tým:N', sort=sort_order), x=alt.value(0), text='Hodnota:Q')
    txt_ob = alt.Chart(df_p[df_p['Typ'] == 'Obdržené']).mark_text(align='right', dx=-10, color='white', fontWeight='bold').encode(y=alt.Y('Tým:N', sort=sort_order), x=alt.X('sum(Hodnota):Q', stack='normalize'), text='Hodnota:Q')
    st.altair_chart((bars + txt_ud + txt_ob).properties(height=700), use_container_width=True)

# --- 5. SEKCE: ROZHODČÍ ---
elif volba == "Rozhodčí":
    st.header("Analýza rozhodčích PL 25/26")
    ref_stats = []
    for r in df_hist['Referee'].unique():
        zref = df_hist[df_hist['Referee'] == r]
        zk = zref['HY'].sum() + zref['AY'].sum()
        ck = zref['HR'].sum() + zref['AR'].sum()
        f = zref['HF'].sum() + zref['AF'].sum()
        ref_stats.append({"Rozhodčí": r, "Zápasy": len(zref), "Fauly/Z": round(f/len(zref),1), "ŽK/Z": round(zk/len(zref),2), "ČK celkem": int(ck)})
    df_ref = pd.DataFrame(ref_stats).sort_values("ŽK/Z", ascending=False).reset_index(drop=True)
    df_ref.index += 1
    st.dataframe(df_ref, use_container_width=True)

# --- 6. SEKCE: SIMULÁTOR ZÁPASŮ ---
# --- 6. SEKCE: SIMULÁTOR ZÁPASŮ (MOBILE FRIENDLY) ---
elif volba == "Simulátor zápasů":
    st.header("Analýza a predikce střetnutí")
    týmy = sorted(df_hist['HomeTeam'].unique())
    
    # Nastavení výchozích hodnot do session_state, pokud tam ještě nejsou
    if 't1_pick' not in st.session_state: st.session_state.t1_pick = týmy[0]
    if 't2_pick' not in st.session_state: st.session_state.t2_pick = týmy[1] if len(týmy) > 1 else týmy[0]
    
    # 1. VÝBĚR TÝMŮ PŘES TLAČÍTKA (bez klávesnice)
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        with st.popover(f"🏠 Domácí: {st.session_state.t1_pick}", use_container_width=True):
            st.radio("Vyber domácí tým:", týmy, key="t1_pick")
            
    with c_btn2:
        with st.popover(f"🚀 Hosté: {st.session_state.t2_pick}", use_container_width=True):
            st.radio("Vyber hostující tým:", týmy, key="t2_pick")
    
    t1 = st.session_state.t1_pick
    t2 = st.session_state.t2_pick

    # Zobrazení log a VS
    logo1, logo2 = LOGA_TYMU.get(t1, ""), LOGA_TYMU.get(t2, "")
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0;">
        <div style="text-align: center; width: 30%;"><img src="{logo1}" width="80"><br><span style="color: gray; font-size: 0.8rem; font-weight: bold;">{t1.upper()}</span></div>
        <div style="text-align: center; width: 40%;"><h1 style="margin: 0; font-size: 2.5rem; color: #555;">VS</h1></div>
        <div style="text-align: center; width: 30%;"><img src="{logo2}" width="80"><br><span style="color: gray; font-size: 0.8rem; font-weight: bold;">{t2.upper()}</span></div>
    </div>
    """, unsafe_allow_html=True)

    # 2. VÝBĚR ROZHODČÍHO (bez klávesnice)
    ref_list = sorted(df_hist['Referee'].unique()) if 'Referee' in df_hist.columns else []
    if 'ref_pick' not in st.session_state and ref_list: st.session_state.ref_pick = ref_list[0]
    
    with st.popover(f"🏁 Rozhodčí: {st.session_state.ref_pick}", use_container_width=True):
        st.radio("Vyber rozhodčího:", ref_list, key="ref_pick")
    
    vybrany_ref = st.session_state.ref_pick

    st.write("---")

    # --- FUNKCE A ZÍSKÁNÍ STATISTIK ---
    def get_stats(team):
        d, v = df_hist[df_hist['HomeTeam'] == team], df_hist[df_hist['AwayTeam'] == team]
        z = len(d) + len(v)
        if z == 0: return {"G_v": 0, "G_i": 0, "R": 0, "K": 0, "F": 0}
        return {
            "G_v": (d['FTHG'].sum() + v['FTAG'].sum()) / z,
            "G_i": (d['FTAG'].sum() + v['FTHG'].sum()) / z,
            "R": (d['HC'].sum() + v['AC'].sum()) / z,
            "K": (d['HY'].sum() + v['AY'].sum()) / z,
            "F": (d['HF'].sum() + v['AF'].sum()) / z
        }

    s1, s2 = get_stats(t1), get_stats(t2)
    
    # --- VÝPOČTY ---
    mu_d = (s1["G_v"] + s2["G_i"]) / 2
    mu_h = (s2["G_v"] + s1["G_i"]) / 2
    celkem_goly = mu_d + mu_h

    
    # Poisson 1-X-2
    p_d, p_h, p_r = 0, 0, 0
    for i in range(11):
        for j in range(11):
            p = poisson_pmf(i, mu_d) * poisson_pmf(j, mu_h)
            if i > j: p_d += p
            elif i < j: p_h += p
            else: p_r += p

    # Rohy
    ocek_rohy_t1 = (s1["R"] + s2["R"]) / 2 
    ocek_rohy_t2 = (s2["R"] + s1["R"]) / 2
    celkem_rohy = ocek_rohy_t1 + ocek_rohy_t2

    # Disciplína
    ref_df = df_hist[df_hist['Referee'] == vybrany_ref]
    ref_zapasu = len(ref_df)
    ref_zk_avg = (ref_df['HY'].sum() + ref_df['AY'].sum()) / ref_zapasu if ref_zapasu > 0 else 0
    ref_f_avg = (ref_df['HF'].sum() + ref_df['AF'].sum()) / ref_zapasu if ref_zapasu > 0 else 0
    
    ocek_karty = (s1["K"] + s2["K"] + ref_zk_avg) / 1.5
    ocek_fauly = (s1["F"] + s2["F"] + ref_f_avg) / 1.5

    # --- ZOBRAZENÍ VÝSLEDKŮ ---
    st.subheader("🎯 Predikce zápasu")
    
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Góly {t1}", round(mu_d, 2))
    c2.metric("Očekávané skóre", f"{round(mu_d)} : {round(mu_h)}")
    c3.metric(f"Góly {t2}", round(mu_h, 2))
    
    o1, o2, o3 = st.columns(3)
    o1.success(f"**Výhra {t1}**\n{round(p_d * 100, 1)} %")
    o2.warning(f"**Remíza**\n{round(p_r * 100, 1)} %")
    o3.error(f"**Výhra {t2}**\n{round(p_h * 100, 1)} %")
    
    st.write("---")
    st.markdown("### 🚩 Rohové kopy")
    r1, r2, r3 = st.columns(3)
    r1.metric(f"Rohy {t1}", round(ocek_rohy_t1, 1))
    r2.metric("CELKEM", round(celkem_rohy, 1))
    r3.metric(f"Rohy {t2}", round(ocek_rohy_t2, 1))

    st.write("---")
    st.markdown("### ⚖️ Disciplína")
    f1, f2, f3 = st.columns(3)
    f1.metric("Předpokládané ŽK", round(ocek_karty, 1))
    f2.metric("Předpokládané FAULY", round(ocek_fauly, 1))
    f3.metric("Průměr faulů Ref.", round(ref_f_avg, 1))

    if celkem_rohy > 10.5: st.info(f"📈 **Aktivní křídla!** ({round(celkem_rohy, 1)} rohů)")
    if ocek_fauly > 25: st.warning(f"⚠️ **Kouskovaná hra!** ({round(ocek_fauly, 1)} faulů)")

         # --- SROVNÁVACÍ TABULKA A FORMA ---
    st.subheader("📊 Srovnání a Forma")
    
    # Získání formy a otočení (nejnovější zápas vlevo)
    f1 = ziskej_formu(t1, df_hist)[::-1]
    f2 = ziskej_formu(t2, df_hist)[::-1]
    
    obsah_formy = """
    <div style="width: 100%; font-family: sans-serif; margin-bottom: 15px; border: 1px solid #f0f2f6; padding: 12px 5px; border-radius: 10px; background-color: #fafafa;">
        <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
            <div style="width: 20%; text-align: left;">
                <img src="{l1}" width="42">
            </div>
            <div style="width: 60%; text-align: center; font-weight: bold; font-size: 1.0rem; color: #31333F;">
                {n1} — {n2}
            </div>
            <div style="width: 20%; text-align: right;">
                <img src="{l2}" width="42">
            </div>
        </div>
        <div style="display: flex; justify-content: center; align-items: center; width: 100%; margin-top: 10px;">
            <div style="width: 43%; text-align: right; font-size: 1.0rem;">
                {forma1}
            </div>
            <div style="width: 14%; text-align: center; color: #ccc; font-size: 0.6rem; font-weight: bold;">
                VS
            </div>
            <div style="width: 43%; text-align: left; font-size: 1.0rem;">
                {forma2}
            </div>
        </div>
    </div>
    """.format(l1=logo1, l2=logo2, n1=t1, n2=t2, forma1=f1, forma2=f2)
    
    st.markdown(obsah_formy, unsafe_allow_html=True)
    st.write("---")
    
        # --- 7. AUTOMATICKÉ TIPY NA SÁZKU ---
    st.subheader("💡 Doporučené tipy")
    
    tipy = []

    # Logika pro Góly (využívá novou proměnnou celkem_goly)
    if celkem_goly > 3.0:
        tipy.append("🔥 **Tip na góly:** Over 2.5 (Očekává se ofenzivní zápas)")
    elif celkem_goly < 2.1:
        tipy.append("🛡️ **Tip na góly:** Under 2.5 (Očekává se defenzivní bitva)")

    # Logika pro Rohy
    if celkem_rohy > 11.0:
        tipy.append("🚩 **Tip na rohy:** Over 10.5 (Týmy hrají hodně přes křídla)")
    elif celkem_rohy < 8.5:
        tipy.append("🚩 **Tip na rohy:** Under 9.5 (Hra se drží spíše ve středu pole)")

    # Logika pro Karty
    if ocek_karty > 4.5:
        tipy.append("🟨 **Tip na karty:** Over 3.5 (Přísný rozhodčí nebo agresivní týmy)")
    elif ocek_karty < 2.5:
        tipy.append("🕊️ **Tip na karty:** Under 3.5 (Klidný zápas bez velkých faulů)")

    # Logika pro BTTS (Both Teams To Score)
    if mu_d > 1.1 and mu_h > 1.1:
        tipy.append("⚽ **Oba dají gól:** ANO (Vysoká pravděpodobnost na obou stranách)")

    # Zobrazení tipů
    if tipy:
        for t in tipy:
            st.info(t)
    else:
        st.write("Pro tento zápas nejsou k dispozici žádné výrazné statistické trendy.")
