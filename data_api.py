import requests
import pandas as pd
from economic_analyzer import INDICATORS


def get_countries():
    url = "https://api.worldbank.org/v2/country?format=json&per_page=300"
    r = requests.get(url).json()
    return {
        c["id"]: c["name"]
        for c in r[1]
        if c["region"]["value"] != "Aggregates"
    }

def get_indicators():
    merged = {}
    for category in INDICATORS.values():
        merged.update(category)
    return merged

def fetch_indicator(country, indicator, start_year, end_year):
    url = (
        f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
        f"?format=json&per_page=1000"
    )
    r = requests.get(url).json()

    if len(r) < 2:
        return pd.DataFrame()

    data = [
        {
            "year": int(item["date"]),
            "value": item["value"],
        }
        for item in r[1]
        if item["value"] is not None
    ]

    df = pd.DataFrame(data)
    df = df[(df["year"] >= start_year) & (df["year"] <= end_year)]
    return df.sort_values("year")