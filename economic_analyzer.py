import requests
import pandas as pd
import ollama
from tabulate import tabulate

OLLAMA_MODEL = "gemma3:4b"  # change to whichever model you have pulled

START_YEAR = 2010
END_YEAR = 2025

# World Bank indicator codes mapped to analysis categories
INDICATORS = {
    # ── Step 1: Short-Term Strength (Cyclical) ──
    "short_term": {
        "NY.GDP.MKTP.KD.ZG": "GDP growth (annual %)",
        "FP.CPI.TOTL.ZG": "Inflation, consumer prices (annual %)",
        "SL.UEM.TOTL.ZS": "Unemployment (% of total labor force)",
    },
    # ── Step 2: Structural Strength (Long-Term) ──
    "structural": {
        "SL.GDP.PCAP.EM.KD": "GDP per person employed (constant 2017 PPP $)",
        "SP.POP.GROW": "Population growth (annual %)",
        "SP.DYN.LE00.IN": "Life expectancy at birth (years)",
        "GB.XPD.RSDV.GD.ZS": "R&D expenditure (% of GDP)",
        "IP.PAT.RESD": "Patent applications (residents)",
    },
    # ── Step 3: Risk Factors ──
    "risk": {
        "GC.DOD.TOTL.GD.ZS": "Central government debt (% of GDP)",
        "BN.CAB.XOKA.GD.ZS": "Current account balance (% of GDP)",
        "NE.EXP.GNFS.ZS": "Exports of goods and services (% of GDP)",
        "NE.IMP.GNFS.ZS": "Imports of goods and services (% of GDP)",
        "CC.EST": "Control of Corruption (estimate)",
        "GE.EST": "Government Effectiveness (estimate)",
    },
}


def get_countries():
    """Fetch list of countries from World Bank API."""
    url = "https://api.worldbank.org/v2/country?format=json&per_page=300"
    r = requests.get(url).json()
    countries = {
        c["id"]: c["name"]
        for c in r[1]
        if c["region"]["value"] != "Aggregates"
    }
    return countries

def fetch_indicator(country_code, indicator, start_year=START_YEAR, end_year=END_YEAR):
    """Fetch a single indicator time-series for one country."""
    url = (
        f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}"
        f"?format=json&per_page=1000"
    )
    try:
        r = requests.get(url, timeout=15).json()
    except Exception:
        return pd.DataFrame()

    if len(r) < 2 or r[1] is None:
        return pd.DataFrame()

    data = [
        {"year": int(item["date"]), "value": item["value"]}
        for item in r[1]
        if item["value"] is not None
    ]

    df = pd.DataFrame(data)
    if df.empty:
        return df
    df = df[(df["year"] >= start_year) & (df["year"] <= end_year)]
    df = df.sort_values("year")
    return df

def fetch_all_indicators(country_code):
    """Fetch every indicator for a country and organise by category."""
    results = {}
    all_indicators = {}
    for cat in INDICATORS:
        all_indicators.update(INDICATORS[cat])

    total = len(all_indicators)
    for idx, (code, label) in enumerate(all_indicators.items(), 1):
        print(f"  [{idx}/{total}] Fetching {label} …")
        df = fetch_indicator(country_code, code)
        if not df.empty:
            results[code] = {
                "label": label,
                "data": df.to_dict(orient="records"),
                "latest": df.iloc[-1]["value"],
                "latest_year": int(df.iloc[-1]["year"]),
            }
        else:
            results[code] = {
                "label": label,
                "data": [],
                "latest": None,
                "latest_year": None,
            }
    return results

def build_data_summary(country_name, raw):
    """Turn raw indicator data into a structured text block."""
    sections = []

    for category, title in [
        ("short_term", "STEP 1 – SHORT-TERM STRENGTH (CYCLICAL)"),
        ("structural", "STEP 2 – STRUCTURAL STRENGTH (LONG-TERM)"),
        ("risk", "STEP 3 – RISK FACTORS"),
    ]:
        lines = [f"\n{'='*60}", title, '='*60]
        for code, label in INDICATORS[category].items():
            entry = raw.get(code)
            if entry and entry["data"]:
                table_data = [
                    [d["year"], f'{d["value"]:.4f}' if isinstance(d["value"], float) else d["value"]]
                    for d in entry["data"]
                ]
                lines.append(f"\n  {label}")
                lines.append(
                    tabulate(table_data, headers=["Year", "Value"], tablefmt="simple", numalign="right")
                )
            else:
                lines.append(f"\n  {label}: No data available")
        sections.append("\n".join(lines))

    header = f"ECONOMIC DATA FOR: {country_name.upper()} ({START_YEAR}–{END_YEAR})"
    return f"\n{header}\n" + "\n".join(sections)

SYSTEM_PROMPT = """You are a senior macroeconomist. You will receive economic data
for a country from the World Bank. Provide a SHORT, punchy analysis using EXACTLY
this format (no extra sections, no bullet points, no lengthy explanation):

Short-Term Strength: [Strong / Moderate / Weak]. <2-3 sentences explaining why,
citing key GDP growth %, inflation %, and unemployment % figures from the data.>

Structural Strength: [Strong / Moderate / Weak]. <2-3 sentences explaining why,
citing productivity, demographic, and innovation numbers from the data.>

Risk Factors: [High / Moderate / Low]. <2-3 sentences explaining why, citing
debt-to-GDP %, current account balance %, and governance scores from the data.>

RULES:
- Each section must be EXACTLY 2-3 sentences. No more.
- Always cite specific numbers from the data.
- Do NOT add any extra sections, scores, ratings, or overall summaries.
- Keep the total response under 200 words."""


def ask_ollama(data_text, model=OLLAMA_MODEL):
    """Send the data to Ollama using the chat API with system/user message roles."""
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": (
                f"Here is the data to analyse:\n\n"
                f"{data_text}\n\n"
                f"Provide your concise analysis now using the exact format specified."
            ),
        },
    ]

    print(f"\n{'─'*60}")
    print(f"Sending data to Ollama ({model}) for analysis …")
    print(f"{'─'*60}\n")

    try:
        full_response = []
        stream = ollama.chat(
            model=model,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            token = chunk["message"]["content"]
            print(token, end="", flush=True)
            full_response.append(token)

        print("\n")
        return "".join(full_response)

    except ollama.ResponseError as e:
        print(f"\n[ERROR] Ollama response error: {e.error}")
        if "not found" in str(e.error).lower():
            print(f"Pull the model first:  ollama pull {model}")
        return None
    except Exception as e:
        error_msg = str(e).lower()
        if "connect" in error_msg or "refused" in error_msg:
            print("\n[ERROR] Could not connect to Ollama.")
            print("Make sure Ollama is running:  ollama serve")
            print(f"And that you have pulled the model:  ollama pull {model}")
        else:
            print(f"\n[ERROR] Ollama request failed: {e}")
        return None
