import pandas as pd
import pickle
from sklearn.ensemble import RandomForestRegressor

df = pd.read_csv("ml_dataset.csv")

targets = [
    "target_fouls_home", "target_fouls_away",
    "target_cards_home", "target_cards_away",
    "target_corners_home", "target_corners_away",
    "target_goals_home", "target_goals_away"
]

feature_cols = [
    "home_strength", "away_strength",
    "home_form", "away_form",
    "home_avg_fouls", "away_avg_fouls",
    "home_avg_cards", "away_avg_cards",
    "home_avg_corners", "away_avg_corners",
    "home_avg_goals", "away_avg_goals",
    "ref_fouls_home", "ref_fouls_away",
    "ref_cards_home", "ref_cards_away",
    "ref_corners_home", "ref_corners_away"
]

X = df[feature_cols]

for target in targets:
    y = df[target]

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=8,
        random_state=42
    )
    model.fit(X, y)

    pickle.dump(model, open(f"{target}.pkl", "wb"))
    print(f"Model {target}.pkl uložen.")
