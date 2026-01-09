import pandas as pd
import requests

url = "https://www.whoscored.com/StatisticsFeed/1/GetTeamStatistics"
stage_id = 18684
headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.whoscored.com"}

def fetch(cat):
    r = requests.get(url, params={"stageId": stage_id, "category": cat}, headers=headers)
    return r.json()["teamTableStats"]

disc = fetch("Discipline")
summ = fetch("Summary")

rows = []
for d, s in zip(disc, summ):
    rows.append({
        "Team": d["name"],
        "Aggression": d["stats"]["aggression"],
        "FoulsCommitted": d["stats"]["foulsCommitted"],
        "FoulsSuffered": d["stats"]["foulsSuffered"],
        "DuelIntensity": s["stats"]["duelIntensity"]
    })

ws = pd.DataFrame(rows)
ws.to_csv("whoscored_cache.csv", index=False)
print("WhoScored CSV uložen ✅")
