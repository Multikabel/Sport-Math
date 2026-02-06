import pandas as pd

# --- 1) NAČTENÍ DAT STEJNĚ JAKO VE STREAMLITU ---
def nacti_data():
    url = "https://www.football-data.co.uk/mmz4281/2526/E0.csv"
    df = pd.read_csv(url)
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
    return df

df_hist = nacti_data()

# --- 2) SÍLA TÝMŮ (A/B/C) ---
def urci_silu_z_df(df_hist, team):
    # spočítáme tabulku stejně jako v appce
    týmy = sorted(df_hist["HomeTeam"].unique())
    tab = []
    for t in týmy:
        d = df_hist[df_hist["HomeTeam"] == t]
        v = df_hist[df_hist["AwayTeam"] == t]
        b = (d["FTR"]=="H").sum()*3 + (d["FTR"]=="D").sum() + (v["FTR"]=="A").sum()*3 + (v["FTR"]=="D").sum()
        sv = d["FTHG"].sum() + v["FTAG"].sum()
        so = d["FTAG"].sum() + v["FTHG"].sum()
        tab.append({"Tým": t, "B": b, "GD": sv-so})

    df_top = pd.DataFrame(tab).sort_values(["B","GD"], ascending=False).reset_index(drop=True)
    df_top.index += 1

    try:
        pozice = df_top[df_top["Tým"] == team].index[0]
        if pozice <= 6:
            return 3
        elif pozice >= 15:
            return 1
        else:
            return 2
    except:
        return 2

# --- 3) FORMA (posledních 5 zápasů) ---
def forma_numeric(team, df):
    last5 = df[(df["HomeTeam"] == team) | (df["AwayTeam"] == team)].sort_values("Date").tail(5)
    score = 0
    for _, r in last5.iterrows():
        if r["HomeTeam"] == team:
            if r["FTHG"] > r["FTAG"]:
                score += 3
            elif r["FTHG"] == r["FTAG"]:
                score += 1
        else:
            if r["FTAG"] > r["FTHG"]:
                score += 3
            elif r["FTAG"] == r["FTHG"]:
                score += 1
    return score

# --- 4) PRŮMĚRNÉ STATISTIKY ---
def avg_stats(team, col_home, col_away):
    mask_h = df_hist["HomeTeam"] == team
    mask_a = df_hist["AwayTeam"] == team
    total = df_hist[mask_h][col_home].sum() + df_hist[mask_a][col_away].sum()
    count = mask_h.sum() + mask_a.sum()
    return total / count if count > 0 else 0

# --- 5) TARGETY ---
df = df_hist.copy()

df["target_fouls_home"] = df["HF"]
df["target_fouls_away"] = df["AF"]

df["target_cards_home"] = df["HY"]
df["target_cards_away"] = df["AY"]

df["target_corners_home"] = df["HC"]
df["target_corners_away"] = df["AC"]

df["target_goals_home"] = df["FTHG"]
df["target_goals_away"] = df["FTAG"]

# --- 6) FEATURES: síla, forma, průměry ---
df["home_strength"] = df["HomeTeam"].apply(lambda t: urci_silu_z_df(df_hist, t))
df["away_strength"] = df["AwayTeam"].apply(lambda t: urci_silu_z_df(df_hist, t))

df["home_form"] = df["HomeTeam"].apply(lambda t: forma_numeric(t, df_hist))
df["away_form"] = df["AwayTeam"].apply(lambda t: forma_numeric(t, df_hist))

df["home_avg_fouls"] = df["HomeTeam"].apply(lambda t: avg_stats(t, "HF", "AF"))
df["away_avg_fouls"] = df["AwayTeam"].apply(lambda t: avg_stats(t, "AF", "HF"))

df["home_avg_cards"] = df["HomeTeam"].apply(lambda t: avg_stats(t, "HY", "AY"))
df["away_avg_cards"] = df["AwayTeam"].apply(lambda t: avg_stats(t, "AY", "HY"))

df["home_avg_corners"] = df["HomeTeam"].apply(lambda t: avg_stats(t, "HC", "AC"))
df["away_avg_corners"] = df["AwayTeam"].apply(lambda t: avg_stats(t, "AC", "HC"))

df["home_avg_goals"] = df["HomeTeam"].apply(lambda t: avg_stats(t, "FTHG", "FTAG"))
df["away_avg_goals"] = df["AwayTeam"].apply(lambda t: avg_stats(t, "FTAG", "FTHG"))

# --- 7) ULOŽENÍ ---
df.to_csv("ml_dataset.csv", index=False)
print("Dataset uložen jako ml_dataset.csv")
