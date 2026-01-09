import requests
import pandas as pd
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}

def get_team_stats(team_id):
    url = f"https://www.whoscored.com/StatisticsFeed/1/GetTeamStatistics?teamId={team_id}&category=summary&subcategory=all&statsAccumulationType=0&isCurrent=true"
    r = requests.get(url, headers=HEADERS)
    data = r.json()

    stats = {}
    for item in data["teamTableStats"]:
        name = item["name"]
        value = item["value"]
        stats[name] = value

    return stats

def get_team_id(team_name):
    # Jednoduchá mapa – doplníme podle potřeby
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
    rows = []

    for team in df_hist["HomeTeam"].unique():
        team_id = get_team_id(team)
        if team_id is None:
            continue

        stats = get_team_stats(team_id)
        time.sleep(2)

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
