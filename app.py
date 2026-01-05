import streamlit as st
import pandas as pd
import os

# CESTY K SOUBORŮM
PATH_HISTORIE = 'PL_2526_komplet_vse.csv'
PATH_TABULKA = 'PL_tabulka_aktualni.csv'
PATH_KALENDAR = 'PL_kalendar_budouci2.csv'

st.set_page_config(page_title="PL Analytika 2026", layout="wide")

st.title("⚽ Fotbalová Analytická Aplikace")


# 1. BOČNÍ PANEL
st.sidebar.header("Navigace")
volba = st.sidebar.radio("Přejít na:", ["Přehled ligy", "Analýza týmu", "Nadcházející zápasy"])

# Načtení dat (ošetřené proti chybám)
def nacti_data(cesta):
    if os.path.exists(cesta):
        try:
            # sep=None a engine='python' zajistí, že si Pandas sám zjistí, 
            # jestli je to čárka, středník nebo tabulátor
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

# 2. HLAVNÍ OBSAH
if volba == "Přehled ligy":
    st.header("Aktuální pořadí Premier League")
    if df_tab is not None:
        # 1. Odstraníme "Unnamed" sloupce (ty, co tam nechceme)
        if "Unnamed: 0" in df_tab.columns:
            df_tab = df_tab.drop(columns=["Unnamed: 0"])

        # 2. Převedeme Body (B) na čísla pro správné řazení
        df_tab['B'] = pd.to_numeric(df_tab['B'], errors='coerce')
        
        # 3. SEŘAZENÍ: Použijeme tvé sloupce "B" a "Skóre"
        # (případně "+/-" pokud chceš řadit podle rozdílu branek)
        if 'B' in df_tab.columns and 'Skóre' in df_tab.columns:
            df_tab = df_tab.sort_values(by=['B', 'Skóre'], ascending=False).reset_index(drop=True)
            
            # 4. Vytvoření čistého sloupce Pořadí
            df_tab.index += 1
            df_tab.insert(0, 'Pořadí', df_tab.index)
            
            # 5. Finální zobrazení
            st.dataframe(df_tab, use_container_width=True, hide_index=True)
        else:
            st.error("Chyba v názvech sloupců. Zkontroluj velké/malé písmo.")
            st.write("Vidím tyto sloupce:", list(df_tab.columns))
            
            
            

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

# 1. UPRAVENÁ FUNKCE (sama pozná čárku i středník)
def nacti_data(cesta):
    if os.path.exists(cesta):
        try:
            # sep=None zajistí automatickou detekci oddělovače
            return pd.read_csv(cesta, sep=None, engine='python', encoding='utf-8-sig')
        except Exception as e:
            st.error(f"Chyba při čtení {cesta}: {e}")
            return None
    else:
        st.warning(f"Soubor {cesta} nebyl v adresáři nalezen.")
        return None
        
# 2. UPRAVENÁ SEKCE PRO KALENDÁŘ
elif volba == "Nadcházející zápasy":
    st.header("📅 Plán příštích utkání")
    
    if df_kal is not None:
        # Odstranění prvního sloupce (často index nebo 'Unnamed')
        # Dropujeme první sloupec podle pozice (iloc)
        df_kal = df_kal.iloc[:, 1:]
        
        # Přejmenování sloupců do češtiny
        # Tady si uprav názvy vpravo podle toho, co přesně máš v CSV
        mapping = {
            'Date': 'Datum',
            'Time': 'Čas',
            'HomeTeam': 'Domácí',
            'AwayTeam': 'Hosté',
            'Venue': 'Stadion'
        }
        # Přejmenuje jen ty sloupce, které v tabulce skutečně najde
        df_kal = df_kal.rename(columns=mapping)
            
        # Zobrazení tabulky
        st.dataframe(
            df_kal, 
            use_container_width=True, 
            hide_index=True
        )
        
        st.info(f"Zobrazeno {len(df_kal)} nadcházejících zápasů.")
    else:
        st.info("Momentálně nejsou k dispozici žádná data o budoucích zápasech.")



