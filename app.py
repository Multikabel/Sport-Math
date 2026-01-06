import streamlit as st
import pandas as pd
import os

# CESTY K SOUBORŮM
PATH_HISTORIE = 'PL_2526_komplet_vse.csv'
PATH_TABULKA = 'PL_tabulka_aktualni.csv'
PATH_KALENDAR = 'PL_kalendar_budouci2.csv'

LOGA_TYMU = {
    "Arsenal": "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg",
    "Aston Villa": "https://play-lh.googleusercontent.com/6J_v7Vn-G477XG1N_vR3S6UvjVnL8pC9pPqI_W6mN6z3P5L5L5L5L5L5L5L5L5L5L5",
    "Bournemouth": "https://upload.wikimedia.org/wikipedia/en/e/e5/AFC_Bournemouth_%282013%29.svg",
    "Brentford": "https://upload.wikimedia.org/wikipedia/en/2/2a/Brentford_FC_crest.svg",
    "Brighton": "https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_%26_Hove_Albion_logo.svg",
    "Burnley": "https://upload.wikimedia.org/wikipedia/en/6/62/Burnley_F.C._Logo.svg",
    "Chelsea": "https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg",
    "Crystal Palace": "https://upload.wikimedia.org/wikipedia/en/a/a2/Crystal_Palace_FC_logo_%282022%29.svg",
    "Everton": "https://upload.wikimedia.org/wikipedia/en/7/7c/Everton_FC_logo.svg",
    "Leeds United": "https://upload.wikimedia.org/wikipedia/en/5/54/Leeds_United_F.C._logo.svg",
    "Leeds": "https://upload.wikimedia.org/wikipedia/en/5/54/Leeds_United_F.C._logo.svg",
    "Liverpool": "https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg",
    "Man City": "https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg",
    "Man United": "https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg",
    "Man Utd": "https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg",
    "Newcastle": "https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg",
    "Nott'm Forest": "https://upload.wikimedia.org/wikipedia/en/e/e5/Nottingham_Forest_F.C._logo.svg",
    "Southampton": "https://upload.wikimedia.org/wikipedia/en/c/c9/Southampton_FC.svg",
    "Spurs": "https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg", # Oprava pro Tottenham
    "Tottenham": "https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg",
    "West Ham": "https://upload.wikimedia.org/wikipedia/en/c/c2/West_Ham_United_FC_logo.svg",
    "Wolves": "https://upload.wikimedia.org/wikipedia/en/f/fc/Wolverhampton_Wanderers.svg",
    "Aston Villa": "https://upload.wikimedia.org/wikipedia/en/f/f9/Aston_Villa_FC_crest_%282016%29.svg",
    "Sunderland": "https://upload.wikimedia.org/wikipedia/en/thumb/6/60/Sunderland_AFC_logo.svg/200px-Sunderland_AFC_logo.svg.png",
    "Fulham": "https://upload.wikimedia.org/wikipedia/en/thumb/3/3f/Fulham_FC_%28shield%29.svg/200px-Fulham_FC_%28shield%29.svg.png",
    "Burnley": "https://upload.wikimedia.org/wikipedia/en/thumb/6/62/Burnley_F.C._Logo.svg/200px-Burnley_F.C._Logo.svg.png"
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
        if "Unnamed: 0" in df_tab.columns:
            df_tab = df_tab.drop(columns=["Unnamed: 0"])

        df_tab['B'] = pd.to_numeric(df_tab['B'], errors='coerce')
        
        if 'B' in df_tab.columns and 'Skóre' in df_tab.columns:
            df_tab = df_tab.sort_values(by=['B', 'Skóre'], ascending=False).reset_index(drop=True)
            df_tab.index += 1
            df_tab.insert(0, 'Pořadí', df_tab.index)
            st.dataframe(df_tab, use_container_width=True, hide_index=True)
        else:
            st.error("Chyba v názvech sloupců. Zkontroluj velké/malé písmo.")

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
        
