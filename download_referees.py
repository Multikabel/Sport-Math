import requests
import pandas as pd
from datetime import datetime

# ESPN league IDs
LEAGUE_IDS = {
    "La Liga": "esp.1",
    "Serie A": "ita.1"
}

def get_referee_for_match(home, away, date, league_code):
    """
    Najde rozhodčího pro daný zápas pomocí ESPN JSON feedu.
    """
    try:
        url = f"https://site.web.api.espn.com/apis/v2/sports/soccer/{league_code}/scoreboard?dates={date}"
        r = requests.get(url, timeout=5)
        data = r.json()

        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            teams = comp.get("competitors", [])

            if len(teams) != 2:
                continue

            t1 = teams[0]["team"]["shortDisplayName"].lower()
            t2 = teams[1]["team"]["shortDisplayName"].lower()

            if home.lower() in t1 or home.lower() in t2:
                if away.lower() in t1 or away.lower() in t2:
                    officials = comp.get("officials", [])
                    if officials:
                        return officials[0].get("displayName", None)

        return None

    except Exception:
        return None


def process_league(csv_path, league_name):
    df = pd.read_csv(csv_path)
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

    league_code = LEAGUE_IDS[league_name]

    referees = []

    for _, row in df.iterrows():
        home = row["HomeTeam"]
        away = row["AwayTeam"]
        date = row["Date"].strftime("%Y%m%d")

        ref = get_referee_for_match(home, away, date, league_code)
        referees.append(ref)

    df["Referee"] = referees
    return df


# --- RUN ---
laliga = process_league("SP1.csv", "La Liga")
laliga.to_csv("referees_laliga.csv", index=False)

seriea = process_league("I1.csv", "Serie A")
seriea.to_csv("referees_seriea.csv", index=False)

print("Hotovo! Soubor referees_laliga.csv a referees_seriea.csv vytvořeny.")
