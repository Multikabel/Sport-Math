import pandas as pd
import streamlit as st
import requests
import io
import altair as alt
import math

# --- 1. POMOCNÉ FUNKCE A KONFIGURACE ---
st.set_page_config(page_title="PL Analytika 2026", layout="wide", page_icon="⚽")

def poisson_pmf(k, mu):
    if mu <= 0: return 1.0 if k == 0 else 0.0
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
        return df
    except: return None

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
if df_hist is None:
    st.error("Nepodařilo se načíst data.")
    st.stop()

# --- GLOBÁLNÍ VÝPOČET TABULKY (Potřebujeme pro určení síly týmů) ---
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
        if pozice <= 6: return 'A'
        elif pozice >= 15: return 'C'
        else: return 'B'
    except: return 'B'

# --- 2. NAVIGACE ---
st.sidebar.title("⚽ SPORT-MATH")
volba = st.sidebar.radio("Sekce:", ["Tabulka PL", "Týmové statistiky", "Rozhodčí", "Simulátor zápasů"])

# --- 3. SEKCE: TABULKA PL ---
if volba == "Tabulka PL":
    st.header("Aktuální pořadí Premier League 25/26")
    tabulka_data = []
    for t in týmy_seznam:
        d, v = df_hist[df_hist['HomeTeam'] == t], df_hist[df_hist['AwayTeam'] == t]
        b = (d['FTR']=='H').sum()*3 + (d['FTR']=='D').sum()*1 + (v['FTR']=='A').sum()*3 + (v['FTR']=='D').sum()*1
        sv, so = (d['FTHG'].sum() + v['FTAG'].sum()), (d['FTAG'].sum() + v['FTHG'].sum())
        forma_str = ziskej_formu(t, df_hist)[::-1]
        tabulka_data.append({"Tým": t, "Z": len(d)+len(v), "Skóre": f"{int(sv)}:{int(so)}", "GD": sv-so, "B": b, "Forma": forma_str})
    
    df_res = pd.DataFrame(tabulka_data).sort_values(by=["B", "GD"], ascending=False).reset_index(drop=True)
    df_res.index += 1
    df_res.insert(0, ' ', df_res['Tým'].map(LOGA_TYMU))

    def styluj_tabulku(x):
        df_s = pd.DataFrame('', index=x.index, columns=x.columns)
        if len(x) >= 4: df_s.iloc[0:4, :] = 'background-color: rgba(30, 144, 255, 0.1)'
        if len(x) >= 17: df_s.iloc[-3:, :] = 'background-color: rgba(255, 69, 0, 0.1)'
        return df_s

    st.dataframe(df_res.style.apply(styluj_tabulku, axis=None), column_config={" ": st.column_config.ImageColumn(" ")}, use_container_width=True)

# --- 4. TÝMOVÉ STATISTIKY (Zkráceno pro přehlednost) ---
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


# --- 5. ROZHODČÍ ---
elif volba == "Rozhodčí":
    st.header("Analýza rozhodčích PL 25/26")
    ref_stats = []
    for r in df_hist['Referee'].unique():
        zref = df_hist[df_hist['Referee'] == r]
        zk, ck, f = (zref['HY'].sum()+zref['AY'].sum()), (zref['HR'].sum()+zref['AR'].sum()), (zref['HF'].sum()+zref['AF'].sum())
        ref_stats.append({"Rozhodčí": r, "Zápasy": len(zref), "Fauly/Z": round(f/len(zref),1), "ŽK/Z": round(zk/len(zref),2), "ČK celkem": int(ck)})
    st.dataframe(pd.DataFrame(ref_stats).sort_values("ŽK/Z", ascending=False), use_container_width=True)

# --- 6. SIMULÁTOR ZÁPASŮ ---
elif volba == "Simulátor zápasů":
    st.header("Analýza a predikce střetnutí")
    if 't1_pick' not in st.session_state: st.session_state.t1_pick = týmy_seznam[0]
    if 't2_pick' not in st.session_state: st.session_state.t2_pick = týmy_seznam[1]
    
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        with st.popover(f"🏠 Domácí: {st.session_state.t1_pick}", use_container_width=True):
            st.radio("Vyber domácí:", týmy_seznam, key="t1_pick")
    with c_btn2:
        with st.popover(f"🚀 Hosté: {st.session_state.t2_pick}", use_container_width=True):
            st.radio("Vyber hosty:", týmy_seznam, key="t2_pick")
    
    t1, t2 = st.session_state.t1_pick, st.session_state.t2_pick
    ref_list = sorted(df_hist['Referee'].unique())
    if 'ref_pick' not in st.session_state: st.session_state.ref_pick = ref_list[0]
    with st.popover(f"🏁 Rozhodčí: {st.session_state.ref_pick}", use_container_width=True):
        st.radio("Vyber rozhodčího:", ref_list, key="ref_pick")
    vybrany_ref = st.session_state.ref_pick

    # VÝPOČET FAULŮ NA ZÁKLADĚ SÍLY TÝMŮ
    sila_t1 = urci_silu(t1)
    sila_t2 = urci_silu(t2)

    def ziskej_ocekavane_fauly_pokrocile(tym, role, sila_soupere):
        if role == 'Home':
            zápasy = df_hist[df_hist['HomeTeam'] == tym].copy()
            zápasy['Sila_Soupere'] = zápasy['AwayTeam'].apply(urci_silu)
            fauly = zápasy[zápasy['Sila_Soupere'] == sila_soupere]['HF']
        else:
            zápasy = df_hist[df_hist['AwayTeam'] == tym].copy()
            zápasy['Sila_Soupere'] = zápasy['HomeTeam'].apply(urci_silu)
            fauly = zápasy[zápasy['Sila_Soupere'] == sila_soupere]['AF']
        return fauly.mean() if not fauly.empty else df_hist[df_hist[role+'Team'] == tym][role[0]+'F'].mean()

    # Faktor rozhodčího
    ligovy_avg_f = (df_hist['HF'].mean() + df_hist['AF'].mean())
    ref_avg_f = df_hist[df_hist['Referee'] == vybrany_ref][['HF', 'AF']].sum(axis=1).mean()
    ref_faktor = ref_avg_f / ligovy_avg_f if ligovy_avg_f > 0 else 1.0

    f_domaci = ziskej_ocekavane_fauly_pokrocile(t1, 'Home', sila_t2)
    f_hoste = ziskej_ocekavane_fauly_pokrocile(t2, 'Away', sila_t1)
    ocek_fauly = (f_domaci + f_hoste) * ref_faktor

    # --- ZBYTEK PŮVODNÍCH VÝPOČTŮ (Góly, Rohy, Karty) ---
    def get_stats(team):
        d, v = df_hist[df_hist['HomeTeam'] == team], df_hist[df_hist['AwayTeam'] == team]
        z = len(d) + len(v)
        return {"G_v": (d['FTHG'].sum()+v['FTAG'].sum())/z, "G_i": (d['FTAG'].sum()+v['FTHG'].sum())/z, 
                "R": (d['HC'].sum()+v['AC'].sum())/z, "K": (d['HY'].sum()+v['AY'].sum())/z}

    st1, st2 = get_stats(t1), get_stats(t2)
    mu_d, mu_h = (st1["G_v"] + st2["G_i"])/2, (st2["G_v"] + st1["G_i"])/2
    celkem_goly = mu_d + mu_h
    ocek_rohy = (st1["R"] + st2["R"])
    ref_zk_avg = (df_hist[df_hist['Referee'] == vybrany_ref]['HY'].sum() + df_hist[df_hist['Referee'] == vybrany_ref]['AY'].sum()) / len(df_hist[df_hist['Referee'] == vybrany_ref])
    ocek_karty = (st1["K"] + st2["K"] + ref_zk_avg) / 1.5

    # Zobrazení log
    st.markdown(f"""<div style="display: flex; justify-content: space-between; align-items: center;"><div style="text-align: center; width: 30%;"><img src="{LOGA_TYMU.get(t1)}" width="80"></div><div style="text-align: center; width: 40%;"><h1>VS</h1></div><div style="text-align: center; width: 30%;"><img src="{LOGA_TYMU.get(t2)}" width="80"></div></div>""", unsafe_allow_html=True)

    # Vizuální metriky
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Góly {t1}", round(mu_d, 2))
    c2.metric("Očekávané skóre", f"{round(mu_d)} : {round(mu_h)}")
    c3.metric(f"Góly {t2}", round(mu_h, 2))
    
    st.write("---")
    f1, f2, f3 = st.columns(3)
    f1.metric("Předpokládané ŽK", round(ocek_karty, 1))
    f2.metric("CELKEM FAULY", round(ocek_fauly, 1))
    f3.metric("Faktor rozhodčího", round(ref_faktor, 2))

    # Karta formy
    st.subheader("📊 Srovnání a Forma")
    forma_html = f"""<div style="display:flex; justify-content:center; align-items:center; gap:20px;"><div>{ziskej_formu(t1,df_hist)[::-1]}</div><div style="color:#ccc">VS</div><div>{ziskej_formu(t2,df_hist)[::-1]}</div></div>"""
    st.markdown(forma_html, unsafe_allow_html=True)

    # Tipy
    st.subheader("💡 Doporučené tipy")
    if ocek_fauly > 24.5: st.warning(f"⚠️ **Vysoká intenzita faulů!** Rozhodčí i herní styly proti síle {sila_t1}/{sila_t2} naznačují Over.")
    if celkem_goly > 3.0: st.info("🔥 **Tip na góly:** Over 2.5")
    if ocek_karty > 4.5: st.error("🟨 **Karty:** Over 3.5")
