import requests
import pandas as pd
import time

# Session s cookies
session = requests.Session()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.whoscored.com/"
}

# Inicializace cookies – nutné!
def init_cookies():
    session.get("https://www.whoscored.com", headers=HEADERS)

def get_team_stats(team_id):
    url = (
        "https://www.whoscored.com/StatisticsFeed/1/GetTeamStatistics"
        f"?teamId={team_id}&category=summary&subcategory=all&statsAccumulationType=0&isCurrent=true"
    )

    r = session.get(url, headers=HEADERS)

    # Pokud to není JSON, vrátí HTML → chyba
    try:
        data = r.json()
    except:
        print(f"WhoScored JSON error for team {team_id}, status {r.status_code}")
        return None

    stats = {}
    for item in data.get("teamTableStats", []):
        stats[item["name"]] = item["value"]

    return stats

def get_team_id(team_name):
    mapping = {
        "Arsenal": 13,
        "Chelsea": 15,
        "Liverpool": 14,
        "Man City": 32,
        "Man United": 33,
        "Tottenham": 18,
        "Newcastle": 23,
        "Brighton": 36,
        "Wolves": 38,
        "West Ham": 21,
        "Aston Villa": 24,
        "Fulham": 31,
        "Everton": 29,
        "Brentford": 130,
        "Bournemouth": 127,
        "Nott'm Forest": 26,
        "Crystal Palace": 27,
        "Leeds": 8,
        "Southampton": 20,
        "Burnley": 43
    }
    return mapping.get(team_name)

def get_whoscored_features(df_hist):
    init_cookies()  # důležité!

    rows = []

    for team in df_hist["HomeTeam"].unique():
        team_id = get_team_id(team)
        if team_id is None:
            continue

        stats = get_team_stats(team_id)
        time.sleep(1.5)

        if stats is None:
            rows.append({
                "Team": team,
                "Aggression": 0,
                "FoulsCommitted": 0,
                "FoulsSuffered": 0,
                "Tackles": 0,
                "AerialDuels": 0,
                "DuelIntensity": 0
            })
            continue

        rows.append({
            "Team": team,
            "Aggression": stats.get("Aggression", 0),
            "FoulsCommitted": stats.get("Fouls committed", 0),
            "FoulsSuffered": stats.get("Fouls suffered", 0),
            "Tackles": stats.get("Tackles", 0),
            "AerialDuels": stats.get("Aerial duels", 0),
            "DuelIntensity": stats.get("Duels", 0)
        })

    return pd.DataFrame(rows)
