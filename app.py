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

# --- GLOBÁLNÍ VÝPOČET TABULKY (Potřebujeme pro určení síly týmů v celém skriptu) ---
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
        # Hledáme pozici v aktuální tabulce
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
    tabulka_final = []
    for t in týmy_seznam:
        d, v = df_hist[df_hist['HomeTeam'] == t], df_hist[df_hist['AwayTeam'] == t]
        b = (d['FTR']=='H').sum()*3 + (d['FTR']=='D').sum()*1 + (v['FTR']=='A').sum()*3 + (v['FTR']=='D').sum()*1
        sv, so = (d['FTHG'].sum() + v['FTAG'].sum()), (d['FTAG'].sum() + v['FTHG'].sum())
        forma_str = ziskej_formu(t, df_hist)[::-1]
        tabulka_final.append({"Tým": t, "Z": len(d)+len(v), "Skóre": f"{int(sv)}:{int(so)}", "GD": sv-so, "B": b, "Forma": forma_str})
    
    df_res = pd.DataFrame(tabulka_final).sort_values(by=["B", "GD"], ascending=False).reset_index(drop=True)
    df_res.index += 1
    df_res.insert(0, ' ', df_res['Tým'].map(LOGA_TYMU))

    def styluj_tabulku(x):
        df_s = pd.DataFrame('', index=x.index, columns=x.columns)
        if len(x) >= 4: df_s.iloc[0:4, :] = 'background-color: rgba(30, 144, 255, 0.1)'
        if len(x) >= 17: df_s.iloc[-3:, :] = 'background-color: rgba(255, 69, 0, 0.1)'
        return df_s

    st.dataframe(df_res.style.apply(styluj_tabulku, axis=None), column_config={" ": st.column_config.ImageColumn(" ")}, use_container_width=True)

# --- 4. TÝMOVÉ STATISTIKY ---
elif volba == "Týmové statistiky":
    metrika = st.radio("Metrika:", ["Žluté karty", "Fauly", "Rohy"], horizontal=True)
    m = {"Žluté karty": ("HY", "AY"), "Fauly": ("HF", "AF"), "Rohy": ("HC", "AC")}[metrika]
    plot_data = []
    for t in týmy_seznam:
        mask_h, mask_a = df_hist['HomeTeam']==t, df_hist['AwayTeam']==t
        z = len(df_hist[mask_h | mask_a])
        ud = (df_hist[mask_h][m[0]].sum() + df_hist[mask_a][m[1]].sum()) / z
        ob = (df_hist[mask_h][m[1]].sum() + df_hist[mask_a][m[0]].sum()) / z
        plot_data.append({"Tým": t, "Typ": "Udělané", "Hodnota": round(ud, 1)})
        plot_data.append({"Tým": t, "Typ": "Obdržené", "Hodnota": round(ob, 1)})
    df_p = pd.DataFrame(plot_data)
    sort_order = alt.EncodingSortField(field="Hodnota", op="sum", order="descending")
    chart = alt.Chart(df_p).mark_bar().encode(
        y=alt.Y('Tým:N', sort=sort_order),
        x=alt.X('Hodnota:Q'),
        color=alt.Color('Typ:N', scale=alt.Scale(range=['#2ca02c', '#d62728']))
    ).properties(height=700)
    st.altair_chart(chart, use_container_width=True)

# --- 5. ROZHODČÍ ---
elif volba == "Rozhodčí":
    st.header("Analýza rozhodčích PL 25/26")
    ref_stats = []
    for r in df_hist['Referee'].unique():
        zref = df_hist[df_hist['Referee'] == r]
        zk = zref['HY'].sum() + zref['AY'].sum()
        f = zref['HF'].sum() + zref['AF'].sum()
        ref_stats.append({"Rozhodčí": r, "Zápasy": len(zref), "Fauly/Z": round(f/len(zref),1), "ŽK/Z": round(zk/len(zref),2)})
    st.dataframe(pd.DataFrame(ref_stats).sort_values("ŽK/Z", ascending=False), use_container_width=True)

# --- 6. SIMULÁTOR ZÁPASŮ ---
elif volba == "Simulátor zápasů":
    st.subheader("Analýza a predikce střetnutí")
    
    # Session state pro výběr týmů
    if 't1_pick' not in st.session_state: st.session_state.t1_pick = týmy_seznam[0]
    if 't2_pick' not in st.session_state: st.session_state.t2_pick = týmy_seznam[1]
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        with st.popover(f"🏠 Domácí: {st.session_state.t1_pick}", use_container_width=True):
            st.radio("Vyber domácí:", týmy_seznam, key="t1_pick")
    with col_t2:
        with st.popover(f"🚀 Hosté: {st.session_state.t2_pick}", use_container_width=True):
            st.radio("Vyber hosty:", týmy_seznam, key="t2_pick")
    
    t1, t2 = st.session_state.t1_pick, st.session_state.t2_pick

    # Úprava rozhodčích (Příjmení Jméno)
    original_refs = df_hist['Referee'].unique()
    ref_mapping = {}
    for r in original_refs:
        if isinstance(r, str) and " " in r:
            parts = r.split(" ")
            formatted = f"{parts[-1]} {' '.join(parts[:-1])}"
            ref_mapping[formatted] = r
        else: ref_mapping[r] = r
    
    ref_display_list = sorted(ref_mapping.keys())
    if 'ref_display_pick' not in st.session_state: st.session_state.ref_display_pick = ref_display_list[0]
    
    with st.popover(f"🏁 Rozhodčí: {st.session_state.ref_display_pick}", use_container_width=True):
        st.radio("Vyber rozhodčího:", ref_display_list, key="ref_display_pick")
    
    vybrany_ref = ref_mapping.get(st.session_state.ref_display_pick)

    # --- POKROČILÉ VÝPOČTY DLE SÍLY SOUPEŘE ---
    sila_t1, sila_t2 = urci_silu(t1), urci_silu(t2)

    def ziskej_stats_sila(tym, role, sila_soupere, sloupec):
        if role == 'Home':
            z = df_hist[df_hist['HomeTeam'] == tym].copy()
            z['Sila_Soupere'] = z['AwayTeam'].apply(urci_silu)
        else:
            z = df_hist[df_hist['AwayTeam'] == tym].copy()
            z['Sila_Soupere'] = z['HomeTeam'].apply(urci_silu)
        
        res = z[z['Sila_Soupere'] == sila_soupere][sloupec]
        return res.mean() if not res.empty else df_hist[df_hist[role+'Team'] == tym][sloupec].mean()

    # 1. Góly (Poisson lambda)
    mu_d = (ziskej_stats_sila(t1, 'Home', sila_t2, 'FTHG') + ziskej_stats_sila(t2, 'Away', sila_t1, 'FTHG')) / 2
    mu_h = (ziskej_stats_sila(t2, 'Away', sila_t1, 'FTAG') + ziskej_stats_sila(t1, 'Home', sila_t2, 'FTAG')) / 2
    celkem_goly = mu_d + mu_h

    # 2. Rohy
    ocek_rohy = ziskej_stats_sila(t1, 'Home', sila_t2, 'HC') + ziskej_stats_sila(t2, 'Away', sila_t1, 'AC')

    # 3. Fauly a Rozhodčí
    ligovy_avg_f = (df_hist['HF'].mean() + df_hist['AF'].mean())
    ref_data = df_hist[df_hist['Referee'] == vybrany_ref]
    ref_avg_f = ref_data[['HF', 'AF']].sum(axis=1).mean() if not ref_data.empty else ligovy_avg_f
    ref_faktor = ref_avg_f / ligovy_avg_f if ligovy_avg_f > 0 else 1.0
    
    f_base = (ziskej_stats_sila(t1, 'Home', sila_t2, 'HF') + ziskej_stats_sila(t2, 'Away', sila_t1, 'AF'))
    ocek_fauly = f_base * ref_faktor

    # 4. Karty
    ref_zk_avg = ref_data[['HY', 'AY']].sum().sum() / len(ref_data) if not ref_data.empty else 3.5
    ocek_karty = ((df_hist[df_hist['HomeTeam']==t1]['HY'].mean() + df_hist[df_hist['AwayTeam']==t2]['AY'].mean()) + ref_zk_avg) / 2

    # --- VIZUALIZACE ---
    st.markdown(f"""<div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0;">
        <div style="text-align: center; width: 30%;"><img src="{LOGA_TYMU.get(t1)}" width="80"><br><span style="color: gray; font-size: 0.8rem; font-weight: bold;">{t1.upper()}</span></div>
        <div style="text-align: center; width: 40%;"><h1 style="margin: 0; font-size: 2.5rem; color: #555;">VS</h1></div>
        <div style="text-align: center; width: 30%;"><img src="{LOGA_TYMU.get(t2)}" width="100"><br><span style="color: gray; font-size: 0.8rem; font-weight: bold;">{t2.upper()}</span></div>
    </div>""", unsafe_allow_html=True)

    # --- 2. FORMA (PŘESUNUTO SEM A ZMENŠENO) ---
    # Zmenšujeme nadpis pomocí <h6> nebo vlastního spanu a puntíky přes font-size
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

        # --- VIZUALIZACE VÝSLEDKŮ (KOMPAKTNÍ ŘÁDEK 1) ---

        # Definice stylu pro tmavé boxy (můžeš dát na začátek simulátoru nebo přímo sem)
    style_box = "background-color: #2b3035; padding: 15px; border-radius: 12px; color: white; margin-bottom: 5px; text-align: center;"

    # 1. HORNÍ BOX (Góly a skóre)
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

    # 2. DOLNÍ BOX (Rohy, Fauly, Karty)
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
    
    
    
    # Tipy
    st.subheader("💡 Doporučené tipy")
    tipy = []
    if celkem_goly > 3.0: tipy.append("🔥 **Góly:** Over 2.5")
    if ocek_rohy > 11.0: tipy.append("🚩 **Rohy:** Over 10.5")
    if ocek_fauly > 24: tipy.append(f"⚠️ **Fauly:** Over 23.5 (Ref faktor: {round(ref_faktor, 2)})")
    if ocek_karty > 4.5: tipy.append("🟨 **Karty:** Over 3.5")
    
    for t in tipy: st.info(t)



    # --- NOVÁ ČÁST: VÝPOČET PRAVDĚPODOBNOSTÍ ---
    # Výpočet pravděpodobnosti výhry 1-X-2
    p_1, p_x, p_2 = 0, 0, 0
    for i in range(10): # simulujeme skóre 0-9 gólů
        for j in range(10):
            p = poisson_pmf(i, mu_d) * poisson_pmf(j, mu_h)
            if i > j: p_1 += p
            elif i < j: p_2 += p
            else: p_x += p
    
    # Výpočet Over 2.5
    prob_over_2_5 = sum(poisson_pmf(i, mu_d) * poisson_pmf(j, mu_h) 
                        for i in range(10) for j in range(10) if i + j > 2.5)

    # --- SEKCE VALUE BETS ---
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
        check_value(p_x, odd_x, "Remíza")
        check_value(p_2, odd_2, f"Výhra {t2}")
        check_value(prob_over_2_5, odd_over, "Over 2.5 gólu")

