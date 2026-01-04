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
        return pd.read_csv(cesta, sep=';')
    return None

df_hist = nacti_data(PATH_HISTORIE)
df_tab = nacti_data(PATH_TABULKA)
df_kal = nacti_data(PATH_KALENDAR)

# 2. HLAVNÍ OBSAH
if volba == "Přehled ligy":
    st.header("Aktuální pořadí Premier League")
    if df_tab is not None:
        st.dataframe(df_tab, use_container_width=True)
    else:
        st.warning("Tabulka ještě nebyla vygenerována.")

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


