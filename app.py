import pandas as pd
import streamlit as st
import requests
import io

# 1. Definice URL adres
URL_STATS = "https://www.football-data.co.uk/mmz4281/2526/E0.csv"
URL_FIXTURES = "https://fixturedownload.com/download/epl-2025-standardized.csv"

@st.cache_data(ttl=3600)
def nacti_vsechna_data():
    # Pomocná funkce pro stahování (FixtureDownload někdy vyžaduje User-Agent)
    def stahni_csv(url):
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Vyhodí chybu, pokud se stažení nepovede
        return pd.read_csv(io.StringIO(response.text))

    # Načtení statistik (Football-Data)
    try:
        df_stats = pd.read_csv(URL_STATS)
    except Exception as e:
        st.warning(f"Nepodařilo se načíst statistiky z Football-Data: {e}")
        df_stats = None

    # Načtení rozpisu (FixtureDownload)
    try:
        df_fix = stahni_csv(URL_FIXTURES)
    except Exception as e:
        st.warning(f"Nepodařilo se načíst rozpis z FixtureDownload: {e}")
        df_fix = None
        
    return df_stats, df_fix

# 2. SAMOTNÉ VOLÁNÍ FUNKCE (Nahraď tímto původní df_hist = ...)
df_hist, df_fixtures = nacti_vsechna_data()



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



# --- ANALÝZA TÝMU (UPRAVENO PRO FOOTBALL-DATA.CO.UK) ---
elif volba == "Analýza týmu":
    metrika = st.radio(
        "Vyberte statistiku:",
        ["Fauly", "Žluté karty", "Rohy"],
        horizontal=True
    )

    # MAPOVÁNÍ NA ZKRATKY FOOTBALL-DATA: 
    # HF=HomeFouls, AF=AwayFouls, HY=HomeYellow, AY=AwayYellow, HC=HomeCorners, AC=AwayCorners
    mapping = {
        "Fauly": {"domaci": "HF", "hoste": "AF", "label": "faulů"},
        "Žluté karty": {"domaci": "HY", "hoste": "AY", "label": "žlutých karet"},
        "Rohy": {"domaci": "HC", "hoste": "AC", "label": "rohů"}
    }

    conf = mapping[metrika]
    
    if df_hist is not None:
        # Football-Data používá sloupce 'HomeTeam' a 'AwayTeam'
        c_dt, c_ht = "HomeTeam", "AwayTeam"
        c_fd, c_fh = conf["domaci"], conf["hoste"]

        if all(c in df_hist.columns for c in [c_dt, c_ht, c_fd, c_fh]):
            týmy = sorted(df_hist[c_dt].unique())
            data_list = []

            for t in týmy:
                # Počet odehraných zápasů týmu v df_hist
                z = len(df_hist[(df_hist[c_dt] == t) | (df_hist[c_ht] == t)])
                if z == 0: continue
                
                # Udělané (vlastní fauly/karty/rohy)
                f_ud = df_hist[df_hist[c_dt] == t][c_fd].sum() + df_hist[df_hist[c_ht] == t][c_fh].sum()
                # Obdržené (soupeřovy fauly/karty/rohy proti týmu)
                f_ob = df_hist[df_hist[c_dt] == t][c_fh].sum() + df_hist[df_hist[c_ht] == t][c_fd].sum()
                
                data_list.append({'Tým': t, 'Typ': 'Udělané', 'Hodnota': f_ud/z})
                data_list.append({'Tým': t, 'Typ': 'Obdržené', 'Hodnota': f_ob/z})

            df_plot = pd.DataFrame(data_list)
            
            # --- Zbytek kódu pro graf (bars + text_ud + text_ob) zůstává stejný ---
            # (Použij ten předchozí stabilní kód s vrstvami)

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
        
