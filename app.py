import streamlit as st
import pandas as pd
import os

# CESTY K SOUBORŮM
PATH_HISTORIE = 'PL_2526_komplet_vse.csv'
PATH_TABULKA = 'PL_tabulka_aktualni.csv'
PATH_KALENDAR = 'PL_kalendar_budouci.csv'

st.set_page_config(page_title="PL Analytika 2026", layout="wide")

st.title("⚽ Fotbalová Analytická Aplikace")


# 1. BOČNÍ PANEL
st.sidebar.header("Navigace")
volba = st.sidebar.radio("Přejít na:", ["Přehled ligy", "Analýza týmu", "Nadcházející zápasy"])

# Načtení dat (ošetřené proti chybám)
def nacti_data(cesta):
    if os.path.exists(cesta):
        try:
            # Načtení se specifikací kódování a středníku
            return pd.read_csv(cesta, sep=';', encoding='utf-8-sig')
        except Exception as e:
            st.error(f"Chyba při čtení {cesta}: {e}")
            return None
    else:
        st.warning(f"Soubor {cesta} nebyl v adresáři nalezen.")
        return None
    

df_hist = nacti_data(PATH_HISTORIE)
df_tab = nacti_data(PATH_TABULKA)
df_kal = nacti_data(PATH_KALENDAR)

# 2. HLAVNÍ OBSAH
if volba == "Přehled ligy":
    st.header("Aktuální pořadí Premier League")
    if df_tab is not None:
        # 1. Odstraníme úplně prázdné sloupce a řádky
        df_tab = df_tab.dropna(how='all', axis=1).dropna(how='all', axis=0)
        
        # 2. Pokud se sloupce jmenují "Unnamed", zkusíme je přejmenovat podle pořadí
        # Předpokládáme pořadí z tvého skriptu: Tým, Z, V, R, P, Skóre (S), Body (B)
        if 'B' not in df_tab.columns:
            # Přejmenujeme sloupce podle pozice (pokud jich máš v CSV 7 nebo 8)
            # Uprav si seznam názvů, pokud jich máš víc/míň
            nove_nazvy = ['Tým', 'Z', 'V', 'R', 'P', 'S', 'B']
            # Pokud je tam navíc indexový sloupec, přidáme ho na začátek
            if len(df_tab.columns) == 8:
                nove_nazvy = ['Starý_Index'] + nove_nazvy
            
            df_tab.columns = nove_nazvy[:len(df_tab.columns)]

        # 3. Vyčištění názvů (pro jistotu)
        df_tab.columns = df_tab.columns.str.strip()

        # 4. Samotné seřazení a zobrazení
        try:
            # Převod na čísla (někdy se načtou jako text a pak se špatně řadí)
            df_tab['B'] = pd.to_numeric(df_tab['B'], errors='coerce')
            df_tab['S'] = pd.to_numeric(df_tab['S'], errors='coerce')
            
            df_tab = df_tab.sort_values(by=['B', 'S'], ascending=False).reset_index(drop=True)
            df_tab.index += 1
            df_tab.insert(0, 'Pořadí', df_tab.index)
            
            st.dataframe(df_tab, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Chyba při zpracování tabulky: {e}")
            st.write("Aktuální sloupce v souboru:", list(df_tab.columns))
            st.dataframe(df_tab) # Ukáže tabulku aspoň v surovém stavu
            
            

elif volba == "Analýza týmu":
    st.header("Detailní statistiky")
    if df_tab is not None:
        tym = st.selectbox("Vyberte tým pro analýzu:", df_tab['Tým'].unique())
        
        # Tady zobrazíme průměry vybraného týmu
        if df_hist is not None:
            zapas_tymu = df_hist[(df_hist['Domaci_Tym'] == tym) | (df_hist['Hoste_Tym'] == tym)]
            st.metric("Odehraných zápasů", len(zapas_tymu))
            
            # Jednoduchý graf střel
            st.subheader("Vývoj střel v sezóně")
            st.line_chart(zapas_tymu[['Strely_Domaci', 'Strely_Hoste']].reset_index(drop=True))
    else:
        st.error("Chybí data pro analýzu.")

elif volba == "Nadcházející zápasy":
    st.header("Kalendář zápasů")
    if df_kal is not None and not df_kal.empty:
        st.table(df_kal)
    else:
        st.info("V nejbližších dnech nejsou plánovány žádné ligové zápasy (možná probíhá reprezentační pauza nebo poháry).")


