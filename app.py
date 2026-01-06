import streamlit as st
import pandas as pd
import os

# CESTY K SOUBORŮM
PATH_HISTORIE = 'PL_2526_komplet_vse.csv'
PATH_TABULKA = 'PL_tabulka_aktualni.csv'
PATH_KALENDAR = 'PL_kalendar_budouci2.csv'


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
    "Leeds": "https://crests.football-data.org/341.png",
    "Liverpool": "https://crests.football-data.org/64.png",
    "Man City": "https://crests.football-data.org/65.png",
    "Manchester City": "https://crests.football-data.org/65.png",
    "Man United": "https://crests.football-data.org/66.png",
    "Man Utd": "https://crests.football-data.org/66.png",
    "Newcastle": "https://crests.football-data.org/67.png",
    "Nott'm Forest": "https://crests.football-data.org/351.png",
    "Southampton": "https://crests.football-data.org/340.png",
    "Spurs": "https://crests.football-data.org/73.png",
    "Sunderland": "https://crests.football-data.org/71.png",
    "Tottenham": "https://crests.football-data.org/73.png",
    "West Ham": "https://crests.football-data.org/563.png",
    "Wolves": "https://crests.football-data.org/76.png"
}




st.set_page_config(page_title="PL Analytika 2026", layout="wide")

st.title("⚽ SPORT-MATH")


# 1. BOČNÍ PANEL
st.sidebar.header("Navigace")
volba = st.sidebar.radio("Přejít na:", ["Přehled ligy", "Analýza týmu", "Nadcházející zápasy"])

# Načtení dat (ošetřené proti chybám - automatická detekce oddělovače)
def nacti_data(cesta):
    if os.path.exists(cesta):
        try:
            # sep=None zajistí, že Pandas sám pozná čárku i středník
            return pd.read_csv(cesta, sep=None, engine='python', encoding='utf-8-sig')
        except Exception as e:
            st.error(f"Chyba při čtení {cesta}: {e}")
            return None
    else:
        st.warning(f"Soubor {cesta} nebyl v adresáři nalezen.")
        return None
    

df_hist = nacti_data(PATH_HISTORIE)
df_tab = nacti_data(PATH_TABULKA)
df_kal = nacti_data(PATH_KALENDAR)

# 2. HLAVNÍ OBSAH - PŘEHLED LIGY
if volba == "Přehled ligy":
    st.header("Aktuální pořadí Premier League")
    if df_tab is not None:
        # 1. Odstraníme "Unnamed" sloupce
        if "Unnamed: 0" in df_tab.columns:
            df_tab = df_tab.drop(columns=["Unnamed: 0"])

        # 2. Převedeme Body (B) na čísla pro správné řazení
        df_tab['B'] = pd.to_numeric(df_tab['B'], errors='coerce')
        
        if 'B' in df_tab.columns and 'Skóre' in df_tab.columns:
            # Seřazení tabulky
            df_tab = df_tab.sort_values(by=['B', 'Skóre'], ascending=False).reset_index(drop=True)
            
            # Vytvoření sloupce Pořadí
            df_tab.index += 1
            df_tab.insert(0, 'Pořadí', df_tab.index)

            # --- PŘIDÁNÍ LOG TÝMŮ ---
            # Vytvoříme sloupec s URL loga na základě názvu týmu
            # .str.strip() vymaže mezery, aby mapování fungovalo
            df_tab.insert(1, 'Logo', df_tab['Tým'].str.strip().map(LOGA_TYMU))
            
            # Diagnostika pro tabulku (kdyby náhodou logo chybělo)
            chybejici_v_tabulce = df_tab[df_tab['Logo'].isna()]['Tým'].unique()
            if len(chybejici_v_tabulce) > 0:
                st.warning(f"Chybí loga pro: {chybejici_v_tabulce}")

            # 3. Zobrazení tabulky s konfigurací pro obrázky
            st.dataframe(
                df_tab, 
                column_config={
                    "Logo": st.column_config.ImageColumn(" ", width="small"),
                    "Pořadí": st.column_config.Column(width="small"),
                    "B": "Body" # Přejmenování sloupce v náhledu
                },
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.error("Chyba v názvech sloupců tabulky.")

# --- ANALÝZA TÝMU (PRŮMĚR NA ZÁPAS S ČÍSLY) ---
# --- ANALÝZA TÝMU (POMĚR FAULŮ) ---
elif volba == "Analýza týmu":
    st.header("📊 Poměr faulů: Udělané vs. Obdržené (na zápas)")
    
    if df_hist is not None:
        # Definice sloupců
        c_dt = "Domaci_Tym"
        c_ht = "Hoste_Tym"
        c_fd = "Fauly_Domaci"
        c_fh = "Fauly_Hoste"

        if all(c in df_hist.columns for c in [c_dt, c_ht, c_fd, c_fh]):
            
            # 1. FAULY UDĚLANÉ (To, co tým spáchal)
            ud_h = df_hist.groupby(c_dt).agg({c_fd: 'sum', c_dt: 'count'}).rename(columns={c_fd: 'F', c_dt: 'Z'}).reset_index()
            ud_a = df_hist.groupby(c_ht).agg({c_fh: 'sum', c_ht: 'count'}).rename(columns={c_fh: 'F', c_ht: 'Z'}).reset_index()
            
            # 2. FAULY OBDRŽENÉ (To, co udělal soupeř týmu)
            ob_h = df_hist.groupby(c_dt).agg({c_fh: 'sum'}).rename(columns={c_fh: 'F'}).reset_index()
            ob_a = df_hist.groupby(c_ht).agg({c_fd: 'sum'}).rename(columns={c_fd: 'F'}).reset_index()

            # Sjednocení do jedné tabulky
            týmy = df_hist[c_dt].unique()
            data_list = []

            for t in týmy:
                zápasy = ud_h[ud_h[c_dt]==t]['Z'].sum() + ud_a[ud_a[c_ht]==t]['Z'].sum()
                f_udělané = ud_h[ud_h[c_dt]==t]['F'].sum() + ud_a[ud_a[c_ht]==t]['F'].sum()
                f_obdržené = ob_h[ob_h[c_dt]==t]['F'].sum() + ob_a[ob_a[c_ht]==t]['F'].sum()
                
                # Přidáme dva řádky pro každý tým (jeden pro Udělané, jeden pro Obdržené)
                data_list.append({'Tým': t, 'Typ': 'Udělané', 'Hodnota': f_udělané/zápasy})
                data_list.append({'Tým': t, 'Typ': 'Obdržené', 'Hodnota': f_obdržené/zápasy})

            df_plot = pd.DataFrame(data_list)

            import altair as alt

            # GRAF
            base = alt.Chart(df_plot).encode(
                y=alt.Y('Tým:N', sort=alt.EncodingSortField(field="Hodnota", op="sum", order="descending"), title="Tým"),
                x=alt.X('Hodnota:Q', title='Průměr faulů na zápas'),
                color=alt.Color('Typ:N', 
                                scale=alt.Scale(domain=['Udělané', 'Obdržené'], range=['#2ca02c', '#d62728']), # Zelená a červená
                                legend=alt.Legend(title="Typ faulů"))
            )

            # Sloupce (Stacked Bar)
            bars = base.mark_bar().properties(height=700)

            # Čísla uvnitř sloupců
            text = base.mark_text(
                align=alt.expr("datum.Typ == 'Udělané' ? 'left' : 'right'"),
                baseline='middle',
                dx=alt.expr("datum.Typ == 'Udělané' ? 5 : -5"),
                color='white',
                fontWeight='bold'
            ).encode(
                text=alt.Text('Hodnota:Q', format='.2f')
            )

            st.altair_chart(bars + text, use_container_width=True)
            
        else:
            st.error("Chyba v detekci sloupců.")



# 4. NADCHÁZEJÍCÍ ZÁPASY
elif volba == "Nadcházející zápasy":
    st.header("📅 Plán příštích utkání")
    
    if df_kal is not None:
        # Odstranění prvního sloupce (indexu)
        df_kal = df_kal.iloc[:, 1:]
        
        # Přejmenování základních sloupců
        mapping = {
            'Date': 'Datum',
            'Time': 'Čas',
            'Home Team': 'Domácí',
            'Away Team': 'Hosté',
            'Location': 'Stadion',
            'Round Number': 'Kolo',
            'Result': 'Výsledek'
        }
        df_kal = df_kal.rename(columns=mapping)

        # 1. Agresivní očištění názvů (pro jistotu)
        df_kal['Domácí'] = df_kal['Domácí'].astype(str).str.strip()
        df_kal['Hosté'] = df_kal['Hosté'].astype(str).str.strip()

        # 2. Mapování log
        df_kal[' '] = df_kal['Domácí'].map(LOGA_TYMU)
        df_kal['  '] = df_kal['Hosté'].map(LOGA_TYMU)

        # 3. DIAGNOSTIKA (Vypíše ti, co přesně chybí)
        chybejici_domaci = df_kal[df_kal[' '].isna()]['Domácí'].unique()
        chybejici_hoste = df_kal[df_kal['  '].isna()]['Hosté'].unique()
        vsechny_chyby = set(list(chybejici_domaci) + list(chybejici_hoste))
        
        if vsechny_chyby:
            st.warning(f"Chybí loga pro tyto týmy: {vsechny_chyby}")

        # Přidání sloupců pro loga (mapování na slovník LOGA_TYMU)
        # .str.strip() vymaže náhodné mezery před/za názvem týmu
        df_kal[' '] = df_kal['Domácí'].str.strip().map(LOGA_TYMU)
        df_kal['  '] = df_kal['Hosté'].str.strip().map(LOGA_TYMU)

        

        # Definice pořadí sloupců (loga jsou u názvů týmů)
        # Sloupce se jmenují ' ' a '  ', aby v tabulce nezabíraly místo textem
        cols_order = ['Datum', 'Čas', ' ', 'Domácí', 'Hosté', '  ', 'Stadion']
        
        # Vybereme jen ty sloupce, které v tabulce po přejmenování skutečně existují
        df_display = df_kal[[c for c in cols_order if c in df_kal.columns]]
            
        # Finální zobrazení tabulky
        st.dataframe(
        df_display, 
        column_config={
                " ": st.column_config.ImageColumn(label=" ", width="small"),
                "  ": st.column_config.ImageColumn(label=" ", width="small"),
            },
            use_container_width=True, 
            hide_index=True
                )
        
        
        st.info(f"Zobrazeno {len(df_kal)} nadcházejících zápasů.")
    else:
        st.info("Momentálně nejsou k dispozici žádná data o budoucích zápasech.")
        
