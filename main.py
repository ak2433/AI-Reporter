from shiny import App, ui, render, reactive
import pandas as pd
import matplotlib.pyplot as plt
from data_api import get_countries, get_indicators, fetch_indicator
from economic_analyzer import (
    fetch_all_indicators,
    build_data_summary,
    ask_ollama,
)

countries = get_countries()
indicators = get_indicators()

app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.link(rel="stylesheet", href="styles.css")
    ),

    ui.h2("🌍 World Bank Indicators Explorer"),

    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select("country", "Country", choices=countries, selected="US"),
            ui.input_select("indicator", "Indicator", choices=indicators, selected="SP.POP.TOTL"),
            ui.input_slider("years", "Year range", min=1960, max=2023, value=(2000, 2020), sep=""),
            ui.input_action_button("load", "Load data"),
            ui.input_action_button("analyze_ai", "Analyze Economic Strength"),
        ),

        ui.card(
            ui.card_header("Indicator data"),
            ui.output_table("data_table"),
        ),

        ui.card(
            ui.card_header("Trend"),
            ui.output_plot("trend_plot"),
        ),

        ui.card(
          ui.card_header("AI Economic Strength Analysis"),
          ui.output_text_verbatim("ai_analysis"),
          class_="mt-3"
        )
    )
)


def server(input, output, session):

    @reactive.calc
    @reactive.event(input.load)
    def data():
        return fetch_indicator(
            input.country(),
            input.indicator(),
            input.years()[0],
            input.years()[1],
        )

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

        for spine in ax.spines.values():
            spine.set_color("#ACC8A2")

        ax.grid(True, color="#ACC8A2", alpha=0.3)

        plt.tight_layout()
        return fig

    @reactive.calc
    @reactive.event(input.analyze_ai)
    def ai_result():
        country_code = input.country()
        country_name = countries[country_code]

        raw = fetch_all_indicators(country_code)
        summary = build_data_summary(country_name, raw)

        response = ask_ollama(summary)
        return response if response else "Analysis failed."

    @output
    @render.text
    def ai_analysis():
        result = ai_result()
        return result if result else "Click 'Analyze Economic Strength' to run AI analysis."

app = App(app_ui, server)

if __name__ == "__main__":
    app.run()