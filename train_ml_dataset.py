import pandas as pd

# --- 1) ZÁKLADNÍ KOPIE ---
df = df_hist.copy()

# --- 2) TARGETY ---
df["target_fouls_home"] = df["HF"]
df["target_fouls_away"] = df["AF"]

df["target_cards_home"] = df["HY"]
df["target_cards_away"] = df["AY"]

df["target_corners_home"] = df["HC"]
df["target_corners_away"] = df["AC"]

df["target_goals_home"] = df["FTHG"]
df["target_goals_away"] = df["FTAG"]

# --- 3) SÍLA TÝMŮ ---
def sila_to_num(s):
    return {"A": 3, "B": 2, "C": 1}.get(s, 2)

df["home_strength"] = df["HomeTeam"].apply(lambda t: sila_to_num(urci_silu(t)))
df["away_strength"] = df["AwayTeam"].apply(lambda t: sila_to_num(urci_silu(t)))

# --- 4) FORMA ---
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

df["home_form"] = df["HomeTeam"].apply(lambda t: forma_numeric(t, df_hist))
df["away_form"] = df["AwayTeam"].apply(lambda t: forma_numeric(t, df_hist))

# --- 5) PRŮMĚRNÉ STATISTIKY ---
def avg_stats(team, col_home, col_away):
    mask_h = df_hist["HomeTeam"] == team
    mask_a = df_hist["AwayTeam"] == team
    total = df_hist[mask_h][col_home].sum() + df_hist[mask_a][col_away].sum()
    count = mask_h.sum() + mask_a.sum()
    return total / count if count > 0 else 0

df["home_avg_fouls"] = df["HomeTeam"].apply(lambda t: avg_stats(t, "HF", "AF"))
df["away_avg_fouls"] = df["AwayTeam"].apply(lambda t: avg_stats(t, "AF", "HF"))

df["home_avg_cards"] = df["HomeTeam"].apply(lambda t: avg_stats(t, "HY", "AY"))
df["away_avg_cards"] = df["AwayTeam"].apply(lambda t: avg_stats(t, "AY", "HY"))

df["home_avg_corners"] = df["HomeTeam"].apply(lambda t: avg_stats(t, "HC", "AC"))
df["away_avg_corners"] = df["AwayTeam"].apply(lambda t: avg_stats(t, "AC", "HC"))

df["home_avg_goals"] = df["HomeTeam"].apply(lambda t: avg_stats(t, "FTHG", "FTAG"))
df["away_avg_goals"] = df["AwayTeam"].apply(lambda t: avg_stats(t, "FTAG", "FTHG"))

# --- 6) ROZHODČÍ ---
if "Referee" in df.columns:
    ref_avg = df.groupby("Referee").agg({
        "HF": "mean",
        "AF": "mean",
        "HY": "mean",
        "AY": "mean",
        "HC": "mean",
        "AC": "mean"
    }).rename(columns={
        "HF": "ref_fouls_home",
        "AF": "ref_fouls_away",
        "HY": "ref_cards_home",
        "AY": "ref_cards_away",
        "HC": "ref_corners_home",
        "AC": "ref_corners_away"
    })

    df = df.merge(ref_avg, on="Referee", how="left")
else:
    df["ref_fouls_home"] = 0
    df["ref_fouls_away"] = 0
    df["ref_cards_home"] = 0
    df["ref_cards_away"] = 0
    df["ref_corners_home"] = 0
    df["ref_corners_away"] = 0

# --- 7) ULOŽENÍ ---
df.to_csv("ml_dataset.csv", index=False)
print("Dataset uložen jako ml_dataset.csv")
