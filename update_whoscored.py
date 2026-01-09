import asyncio
from playwright.async_api import async_playwright
import requests
import pandas as pd

TEAM_IDS = {
    "Arsenal": 13,
    "Man City": 32,
    "Aston Villa": 24,
    "Liverpool": 14,
    "Chelsea": 15,
    "Man United": 33,
    "Sunderland": 31,
    "Everton": 29,
    "Brentford": 130,
    "Crystal Palace": 27,
    "Fulham": 31,
    "Tottenham": 18,
    "Newcastle": 23,
    "Brighton": 36,
    "Bournemouth": 127,
    "Leeds": 8,
    "Nott'm Forest": 26,
    "West Ham": 21,
    "Burnley": 43,
    "Wolves": 38
}

async def get_cookies():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # první běh necháme viditelný
        context = await browser.new_context()
        page = await context.new_page()

        print("Oteviram WhoScored...")
        await page.goto("https://www.whoscored.com", timeout=60000)

        print("Cekam na JS challenge...")
        await page.wait_for_timeout(8000)

        cookies = await context.cookies()
        await browser.close()

        return {c["name"]: c["value"] for c in cookies}

def fetch_stats(team, team_id, cookies):
    url = (
        "https://www.whoscored.com/StatisticsFeed/1/GetTeamStatistics"
        f"?teamId={team_id}&category=summary&subcategory=all&statsAccumulationType=0&isCurrent=true"
    )

    response = requests.get(url, cookies=cookies, headers={"User-Agent": "Mozilla/5.0"})
    data = response.json()

    stats = {item["name"]: item["value"] for item in data.get("teamTableStats", [])}

    return {
        "Team": team,
        "Aggression": stats.get("Aggression", 0),
        "FoulsCommitted": stats.get("Fouls committed", 0),
        "FoulsSuffered": stats.get("Fouls suffered", 0),
        "Tackles": stats.get("Tackles", 0),
        "AerialDuels": stats.get("Aerial duels", 0),
        "DuelIntensity": stats.get("Duels", 0)
    }

async def main():
    cookies = await get_cookies()

    rows = []
    for team, team_id in TEAM_IDS.items():
        print(f"Stahuju statistiky pro {team}...")
        row = fetch_stats(team, team_id, cookies)
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv("whoscored_cache.csv", index=False)
    print("Hotovo! whoscored_cache.csv ulozen.")

asyncio.run(main())
