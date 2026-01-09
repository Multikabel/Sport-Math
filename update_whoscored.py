import pandas as pd
from whoscored import get_whoscored_features

# Načteme football-data (jen kvůli seznamu týmů)
df = pd.read_csv("https://www.football-data.co.uk/mmz4281/2526/E0.csv")

# Stáhneme WhoScored data
df_ws = get_whoscored_features(df)

# Uložíme cache
df_ws.to_csv("whoscored_cache.csv", index=False)

print("WhoScored cache updated.")
