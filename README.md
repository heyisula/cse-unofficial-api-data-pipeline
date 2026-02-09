# Colombo Stock Exchange (CSE) Unofficial API & Data Pipeline 📈

> **Unofficial API usage guide & Python Data Pipeline 🐍**  
> Explore stock market data from the Colombo Stock Exchange (CSE) via their public API endpoints. This project provides both documentation for the reverse-engineered API and a production-ready pipeline to collect near-real-time market data.

---

<b>Visit <a href='https://heyisula.github.io/cse_unofficial_api_data_pipeline/'>this link</a> to see web view<b>

## Overview 📋

The Colombo Stock Exchange provides market data via several public endpoints used by their web portal. This repository serves two purposes:
1.  **API Documentation**: Documents known endpoints, parameters, and response formats.
2.  **Data Pipeline**: A robust Python application to poll, clean, and store market data for analysis or ML applications.

**Important**: Due to the absence of an official streaming API and the presence of session-protected endpoints, near-real-time market data ingestion was implemented using periodic polling of publicly accessible CSE endpoints.

---

## 🚀 Data Pipeline Features

We have built a fully automated, production-ready pipeline to build your own historical dataset.

*   **Near-Real-Time Polling**: Fetches data every 60 seconds (1 minute) during market hours using standard HTTP requests
*   **Time-Series Storage**: Each poll creates a new timestamped file (append-only, no overwrites)
*   **ISO 8601 Timestamps**: All records include timezone-aware timestamps for Sri Lanka (UTC+5:30)
*   **Session Management**: Mimics a real browser session to reliably access protected endpoints
*   **Rate Limiting**: Respectful 0.4s delays between requests to prevent server overload
*   **Market Hours Aware**: Automatically sleeps when market is closed (weekends and after hours)
*   **Symbol Reference Table**: Daily-refreshed mapping of symbols to company names and sectors
*   **ML-Ready Dataset**: Structured for time-series analysis, feature engineering, and backtesting
*   **Dual Storage** (optional):
    *   **Time-Series**: Endpoint-specific directories with `YYYY-MM-DD_HH-MM.json` files
    *   **Legacy CSV**: Optional append-only CSV for backward compatibility

### 📁 Project Structure

*   **`main.py`**: The entry point. Orchestrates the near-real-time polling loop.
*   **`fetcher.py`**: Logic for session management, API calls, and rate limiting.
*   **`storage.py`**: Handles time-series storage and optional legacy CSV/JSON formats.
*   **`config.py`**: Centralized configuration (polling interval, market hours, endpoints).
*   **`data/`**: Directory where your datasets are stored (ignored by Git).
    *   **`todaySharePrice/`**: Price snapshots by minute
    *   **`tradeSummary/`**: Trade volume and counts
    *   **`marketSummery/`**: Market-level metrics
    *   **`aspiData/`**: ASPI index history
    *   **`snpData/`**: S&P SL20 index history
    *   **`topGainers/`**: Top gaining stocks
    *   **`topLooses/`**: Top losing stocks
    *   **`reference/`**: Symbol metadata (company names, sectors)
*   **`apiweb/`**: Assets for the documentation web view.

### 🛠️ How to Run the Pipeline

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Settings** (optional):
    Edit `config.py` to adjust polling interval, market hours, or enable legacy CSV.

3.  **Start the Collector**:
    ```bash
    python main.py
    ```
    The script will:
    - Log progress to console and `cse_pipeline.log`
    - Poll every 60 seconds during market hours (09:00 - 14:35 SLT)
    - Create timestamped files for each endpoint
    - Sleep when market is closed

4.  **Access Data**:
    Data is saved in `data/` directory with structure:
    ```
    data/
    ├── todaySharePrice/
    │   ├── 2026-02-09_10-00.json
    │   ├── 2026-02-09_10-01.json
    │   └── ...
    ├── marketSummery/
    ├── aspiData/
    └── reference/
        └── symbol_metadata.json
    ```

---

## 🔗 API Endpoints

Base URL: `https://www.cse.lk/api/`

### ✅ Approved Endpoints (Production-Safe)

These endpoints are stable, publicly accessible, and do not require session-specific parameters.

| Endpoint | Description | Method | Key Params |
| :--- | :--- | :--- | :--- |
| `marketStatus` | Check if market is Open/Closed | POST | - |
| `marketSummery` | Market-wide stats (ASPI, Val, Vol) | POST | - |
| `todaySharePrice` | List of all currently active stocks | POST | - |
| `companyInfoSummery` | Detailed info (Price, Vol, Cap) | POST | `symbol` |
| `tradeSummary` | Summary of trades for all securities | POST | - |
| `topGainers` | List of top gaining stocks | POST | - |
| `topLooses` | List of top losing stocks | POST | - |
| `aspiData` | All Share Price Index history | POST | - |
| `snpData` | S&P SL20 Index history | POST | - |
| `allSectors` | Sector index data | POST | - |

### ❌ Blacklisted Endpoints (DO NOT USE)

These endpoints are **unstable** and **not suitable for automation**:

- `chartData` - Requires hidden `chartId` and internal security IDs
- `companyChartDataByStock` - Requires unstable `stockId` (not symbol)
- `detailedTrades` - Session-guarded, rate-limited, returns empty data
- `mostActiveTrades` - Part of protected endpoint group

> **Note**: Most endpoints require a valid session cookie (JSESSIONID) or specific headers (`Origin`, `Referer`, `X-Requested-With`) to work. See `fetcher.py` for a working implementation.

visit <a href='https://github.com/heyisula/cse_unofficial_api_data_pipeline/blob/main/api_endpoint_urls.txt'>this link</a> to view all complete endpoint urls.

---

## ⚠️ Disclaimer

-   **Unofficial**: This project is NOT affiliated with, endorsed by, or connected to the Colombo Stock Exchange.
-   **Educational Use Only**: This code is intended for educational purposes to demonstrate API interaction and data processing.
-   **Data Accuracy**: Data fetched via these unofficial endpoints may not be real-time or accurate. Always verify with official sources.
-   **Server Load**: The pipeline implements delays to be respectful. Do not remove these delays or attempt to scrape data aggressively, as this may disrupt the service for others and result in IP bans.

---

## Contribution 🤝

If you discover new endpoints or better ways to handle the data, please submit a **Pull Request**! Help expand the community knowledge about the CSE API. 🚀

---

## Acknowledgements 🙏

Forked from [GH0STH4CKER/Colombo-Stock-Exchange-CSE-API-Documentation](https://github.com/GH0STH4CKER/Colombo-Stock-Exchange-CSE-API-Documentation).
Special thanks to the original author for the initial reverse engineering work.

---

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
