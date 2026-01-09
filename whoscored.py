import requests
import pandas as pd
import time
import random

# Rotace User-Agentů
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/121.0",
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": "https://www.whoscored.com/",
        "Origin": "https://www.whoscored.com",
        "Connection": "keep-alive",
    }

session = requests.Session()

def init_cookies():
    """Inicializace cookies z homepage WhoScored."""
    try:
        session.get("https://www.whoscored.com", headers=get_headers(), timeout=10)
    except:
        pass

def get_team_stats(team_id):
    """Stáhne statistiky týmu s retry mechanismem."""
    url = (
        "https://www.whoscored.com/StatisticsFeed/1/GetTeamStatistics"
        f"?teamId={team_id}&category=summary&subcategory=all&statsAccumulationType=0&isCurrent=true"
    )

    for attempt in range(3):
        try:
            r = session.get(url, headers=get_headers(), timeout=15)

            # Pokud WhoScored vrátí HTML → blokace
            if "<html" in r.text.lower():
                print(f"Blocked (HTML) for team {team_id}, attempt {attempt+1}")
                time.sleep(random.uniform(2.0, 4.0))
                continue

            data = r.json()

            stats = {}
            for item in data.get("teamTableStats", []):
                stats[item["name"]] = item["value"]

            return stats

        except Exception as e:
            print(f"Error for team {team_id}, attempt {attempt+1}: {e}")
            time.sleep(random.uniform(2.0, 4.0))

    # Po 3 pokusech vrátíme None
    return None

def get_team_id(team_name):
    mapping = {
        "Arsenal": 13, "Chelsea": 15, "Liverpool": 14, "Man City": 32,
        "Man United": 33, "Tottenham": 18, "Newcastle": 23, "Brighton": 36,
        "Wolves": 38, "West Ham": 21, "Aston Villa": 24, "Fulham": 31,
        "Everton": 29, "Brentford": 130, "Bournemouth": 127,
        "Nott'm Forest": 26, "Crystal Palace": 27, "Leeds": 8,
        "Southampton": 20, "Burnley": 43
    }
    return mapping.get(team_name)

def get_whoscored_features(df_hist):
    init_cookies()

    rows = []

    for team in df_hist["HomeTeam"].unique():
        team_id = get_team_id(team)
        if team_id is None:
            continue

        print(f"Downloading WhoScored stats for {team} (ID {team_id})...")
        stats = get_team_stats(team_id)

        # Náhodné zpoždění 1.5–3.5 s
        time.sleep(random.uniform(1.5, 3.5))

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
