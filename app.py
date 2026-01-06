import streamlit as st
import pandas as pd
import os

# CESTY K SOUBORŮM
PATH_HISTORIE = 'PL_2526_komplet_vse.csv'
PATH_TABULKA = 'PL_tabulka_aktualni.csv'
PATH_KALENDAR = 'PL_kalendar_budouci2.csv'


LOGA_TYMU = {
    "Arsenal": "https://play-lh.googleusercontent.com/9m0-z_Uo373Xn09P1T40XbE_W4K_36nOaL66H4WvP_Hl3_Dq1hG_M_qXvV-WbO9e9A=w240-h480-rw",
    "Aston Villa": "https://img.vavel.com/t-aston-villa-logo-png-4336-1603912197545.png",
    "Bournemouth": "https://upload.wikimedia.org/wikipedia/en/e/e5/AFC_Bournemouth_%282013%29.svg",
    "Brentford": "https://upload.wikimedia.org/wikipedia/en/2/2a/Brentford_FC_crest.svg",
    "Brighton": "https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_%26_Hove_Albion_logo.svg",
    "Burnley": "https://crests.football-data.org/70.png",
    "Chelsea": "https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg",
    "Crystal Palace": "https://upload.wikimedia.org/wikipedia/en/a/a2/Crystal_Palace_FC_logo_%282022%29.svg",
    "Everton": "https://upload.wikimedia.org/wikipedia/en/7/7c/Everton_FC_logo.svg",
    "Fulham": "https://crests.football-data.org/63.png",
    "Leeds United": "https://crests.football-data.org/341.png",
    "Liverpool": "https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg",
    "Man City": "https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg",
    "Man Utd": "https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg",
    "Newcastle": "https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg",
    "Nott'm Forest": "https://upload.wikimedia.org/wikipedia/en/e/e5/Nottingham_Forest_F.C._logo.svg",
    "Southampton": "https://upload.wikimedia.org/wikipedia/en/c/c9/Southampton_FC.svg",
    "Spurs": "https://crests.football-data.org/73.png",
    "Sunderland": "https://crests.football-data.org/71.png",
    "Tottenham": "https://crests.football-data.org/73.png",
    "West Ham": "https://upload.wikimedia.org/wikipedia/en/c/c2/West_Ham_United_FC_logo.svg",
    "Wolves": "https://upload.wikimedia.org/wikipedia/en/f/fc/Wolverhampton_Wanderers.svg"
}



st.set_page_config(page_title="PL Analytika 2026", layout="wide")

st.title("⚽ Fotbalová Analytická Aplikace")


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
            
# 3. ANALÝZA TÝMU
elif volba == "Analýza týmu":
    st.header("Detailní statistiky")
    if df_tab is not None:
        tym = st.selectbox("Vyberte tým pro analýzu:", df_tab['Tým'].unique())
        
        if df_hist is not None:
            zapas_tymu = df_hist[(df_hist['Domaci_Tym'] == tym) | (df_hist['Hoste_Tym'] == tym)]
            st.metric("Odehraných zápasů", len(zapas_tymu))
            
            st.subheader("Vývoj střel v sezóně")
            st.line_chart(zapas_tymu[['Strely_Domaci', 'Strely_Hoste']].reset_index(drop=True))
    else:
        st.error("Chybí data pro analýzu.")

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
        
