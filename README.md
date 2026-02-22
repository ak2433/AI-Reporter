# AI Reporter — World Bank Indicators Explorer

A Shiny for Python dashboard that visualizes World Bank economic indicators and generates AI-powered macroeconomic analysis using a local Ollama LLM.

Users select a country, indicator, and year range to load time-series data, view an interactive trend chart, and optionally run a structured economic strength analysis across short-term, structural, and risk dimensions.

---

## Data Summary

All data is fetched live from the [World Bank Open Data API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api). No local dataset is stored.

### Indicator Explorer (sidebar selection)

| Column | Data Type | Description |
|--------|-----------|-------------|
| `year` | `int` | Calendar year of the observation (filtered to the user-selected range) |
| `value` | `float` | Numeric value of the selected indicator for that year |

### AI Economic Strength Analysis (fetched automatically when analysis is triggered)

The analysis button fetches **14 additional indicators** organised into three categories. Each indicator produces the same `year` / `value` columns shown above.

| Category | Indicator Code | Description |
|----------|---------------|-------------|
| **Short-Term** | `NY.GDP.MKTP.KD.ZG` | GDP growth (annual %) |
| | `FP.CPI.TOTL.ZG` | Inflation, consumer prices (annual %) |
| | `SL.UEM.TOTL.ZS` | Unemployment (% of total labor force) |
| **Structural** | `SL.GDP.PCAP.EM.KD` | GDP per person employed (constant 2017 PPP $) |
| | `SP.POP.GROW` | Population growth (annual %) |
| | `SP.DYN.LE00.IN` | Life expectancy at birth (years) |
| | `GB.XPD.RSDV.GD.ZS` | R&D expenditure (% of GDP) |
| | `IP.PAT.RESD` | Patent applications (residents) |
| **Risk** | `GC.DOD.TOTL.GD.ZS` | Central government debt (% of GDP) |
| | `BN.CAB.XOKA.GD.ZS` | Current account balance (% of GDP) |
| | `NE.EXP.GNFS.ZS` | Exports of goods and services (% of GDP) |
| | `NE.IMP.GNFS.ZS` | Imports of goods and services (% of GDP) |
| | `CC.EST` | Control of Corruption (estimate) |
| | `GE.EST` | Government Effectiveness (estimate) |

---

## Technical Details

### API

| Detail | Value |
|--------|-------|
| Provider | World Bank Open Data |
| Base URL | `https://api.worldbank.org/v2/` |
| Auth | **None** — the API is free and requires no key |
| Format | JSON (`?format=json`) |
| Key endpoints | `/country` (country list), `/country/{code}/indicator/{indicator}` (time-series data) |

### Local LLM (Ollama)

The AI analysis feature sends a structured data summary to a locally running [Ollama](https://ollama.com/) instance. No data leaves your machine.

| Detail | Value |
|--------|-------|
| Default model | `gemma3:4b` (configurable in `economic_analyzer.py`) |
| Connection | `localhost:11434` (Ollama default) |

### Packages

| Package | Purpose |
|---------|---------|
| `shiny` | Web application framework (Shiny for Python) |
| `pandas` | Data manipulation and DataFrames |
| `matplotlib` | Trend chart rendering |
| `requests` | HTTP requests to the World Bank API |
| `ollama` | Python client for the local Ollama LLM |
| `tabulate` | Formats indicator data into readable text tables for the LLM prompt |

### File Structure

```
AI-Reporter/
├── main.py                 # Shiny app UI and server logic
├── data_api.py             # World Bank API helpers (countries, indicators, fetch)
├── economic_analyzer.py    # Multi-indicator fetch, summary builder, Ollama integration
├── styles.css              # Custom dark-theme stylesheet
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## Usage Instructions

### Prerequisites

- **Python 3.10+**
- **Ollama** installed and running (only required for the AI analysis feature)

### 1. Clone the repository

```bash
git clone <repo-url>
cd AI-Reporter
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up Ollama (for AI analysis)

Install Ollama from [ollama.com](https://ollama.com/), then pull the default model:

```bash
ollama pull gemma3:4b
```

Make sure the Ollama server is running before using the analysis feature:

```bash
ollama serve
```

> You can swap the model by changing the `OLLAMA_MODEL` variable at the top of `economic_analyzer.py`.

### 5. Run the app

```bash
shiny run main.py
```

The app will open in your browser (typically at `http://127.0.0.1:8000`). From there:

1. **Select** a country and indicator from the sidebar dropdowns.
2. **Adjust** the year range slider.
3. Click **Load data** to fetch and display the data table and trend chart.
4. Click **Analyze Economic Strength** to run the AI-powered macroeconomic analysis.
