from shiny import App, ui, render, reactive
import requests
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Helper functions
# -----------------------------

def get_countries():
    """Fetch list of countries from World Bank API"""
    url = "https://api.worldbank.org/v2/country?format=json&per_page=300"
    r = requests.get(url).json()
    countries = {
        c["id"]: c["name"]
        for c in r[1]
        if c["region"]["value"] != "Aggregates"
    }
    return countries


def get_indicators():
    """Fetch a small subset of indicators (for demo)"""
    # You can expand this or fetch dynamically if you want
    return {
        "SP.POP.TOTL": "Population, total",
        "NY.GDP.MKTP.CD": "GDP (current US$)",
        "SP.DYN.LE00.IN": "Life expectancy at birth",
        "EN.ATM.CO2E.PC": "CO2 emissions (metric tons per capita)",
    }


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
    df = df.sort_values("year")
    return df


# -----------------------------
# UI
# -----------------------------

countries = get_countries()
indicators = get_indicators()

# Custom theme: background #1A2517, accent #ACC8A2
app_css = """
body, .container-fluid, .content {
  background-color: #1A2517 !important;
}
.shiny-bound-output, .card, .bslib-card {
  background-color: #1A2517 !important;
  border-color: #ACC8A2 !important;
  color: #E8EDE6 !important;
}
.card-header {
  background-color: #2a3d24 !important;
  border-color: #ACC8A2 !important;
  color: #ACC8A2 !important;
}
.sidebar {
  background-color: #2a3d24 !important;
  border-color: #ACC8A2 !important;
}
.sidebar .form-label, .sidebar label {
  color: #ACC8A2 !important;
}
.sidebar .form-select, .sidebar .form-control {
  background-color: #1A2517 !important;
  border-color: #ACC8A2 !important;
  color: #E8EDE6 !important;
}
/* Year range slider – blue (match Load data button) */
.sidebar input[type="range"],
.sidebar .irs-line, .sidebar .irs-bar,
.sidebar .irs-single, .sidebar .irs-from, .sidebar .irs-to {
  --slider-blue: #0d6efd;
}
.sidebar input[type="range"]::-webkit-slider-thumb {
  background: #0d6efd !important;
}
.sidebar input[type="range"]::-moz-range-thumb {
  background: #0d6efd !important;
}
.irs-bar, .irs-single, .irs-from, .irs-to { background: #0d6efd !important; border-color: #0d6efd !important; }
.irs-handle { border-color: #0d6efd !important; }
.btn-primary, .btn-action-button, [class*="btn-primary"] {
  background-color: #ACC8A2 !important;
  border-color: #ACC8A2 !important;
  color: #1A2517 !important;
}
.btn-primary:hover, .btn-action-button:hover {
  background-color: #8fb88a !important;
  border-color: #8fb88a !important;
  color: #1A2517 !important;
}
/* Load data button – same blue as year range */
#load, button#load, .sidebar #load {
  background-color: transparent !important;
  border: 2px solid #0d6efd !important;
  color: #0d6efd !important;
  font-weight: 700 !important;
  font-size: 1.1rem !important;
  padding: 0.6rem 1.25rem !important;
  border-radius: 8px !important;
  box-shadow: 0 4px 14px rgba(13, 110, 253, 0.35), 0 0 0 1px rgba(13, 110, 253, 0.2) !important;
  transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}
#load:hover, button#load:hover, .sidebar #load:hover {
  background-color: rgba(13, 110, 253, 0.15) !important;
  border-color: #0d6efd !important;
  color: #0d6efd !important;
  transform: translateY(-2px) !important;
  box-shadow: 0 6px 20px rgba(13, 110, 253, 0.45), 0 0 12px rgba(13, 110, 253, 0.25) !important;
}
#load:active, button#load:active, .sidebar #load:active {
  transform: translateY(0) !important;
}
h2, .card-title {
  color: #ACC8A2 !important;
}
.table, .table td, .table th {
  background-color: #1A2517 !important;
  border-color: #ACC8A2 !important;
  color: #E8EDE6 !important;
}
/* Indicator data table: year and value columns left-aligned */
#data_table th, #data_table td,
#data_table table th, #data_table table td {
  text-align: left !important;
}
"""

app_ui = ui.page_fluid(
    ui.tags.head(ui.tags.style(app_css)),
    ui.h2("🌍 World Bank Indicators Explorer"),

    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select(
                "country",
                "Country",
                choices=countries,
                selected="US",
            ),
            ui.input_select(
                "indicator",
                "Indicator",
                choices=indicators,
                selected="SP.POP.TOTL",
            ),
            ui.input_slider(
                "years",
                "Year range",
                min=1960,
                max=2023,
                value=(2000, 2020),
                sep="",
            ),
            ui.input_action_button("load", "Load data"),
        ),

        ui.card(
            ui.card_header("Indicator data"),
            ui.output_table("data_table"),
        ),

        ui.card(
            ui.card_header("Trend"),
            ui.output_plot("trend_plot"),
        ),
    )
)

# -----------------------------
# Server
# -----------------------------

def server(input, output, session):

    @reactive.calc
    @reactive.event(input.load)
    def data():
        df = fetch_indicator(
            input.country(),
            input.indicator(),
            input.years()[0],
            input.years()[1],
        )
        return df

    @output
    @render.table
    def data_table():
        df = data()
        if df.empty:
            return pd.DataFrame({"Message": ["No data available"]})
        return df

    @output
    @render.plot
    def trend_plot():
        df = data()
        if df.empty:
            return

        fig, ax = plt.subplots(figsize=(7, 4), facecolor="#1A2517")
        ax.set_facecolor("#1A2517")
        ax.plot(df["year"], df["value"], marker="o", color="#ACC8A2", linewidth=2)
        ax.set_title(indicators[input.indicator()], color="#ACC8A2")
        ax.set_xlabel("Year", color="#E8EDE6")
        ax.set_ylabel("Value", color="#E8EDE6")
        ax.tick_params(colors="#E8EDE6")
        ax.spines["bottom"].set_color("#ACC8A2")
        ax.spines["top"].set_color("#ACC8A2")
        ax.spines["left"].set_color("#ACC8A2")
        ax.spines["right"].set_color("#ACC8A2")
        ax.grid(True, color="#ACC8A2", alpha=0.3)
        plt.tight_layout()


# -----------------------------
# Run app
# -----------------------------

app = App(app_ui, server)
if __name__ == "__main__":
    app.run()