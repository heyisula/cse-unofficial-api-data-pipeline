# Colombo Stock Exchange (CSE) Unofficial API & Data Pipeline 📈

> **Unofficial API usage guide & Python Data Pipeline 🐍**  
> Explore stock market data from the Colombo Stock Exchange (CSE) via their public API endpoints. This project provides both documentation for the reverse-engineered API and a production-ready pipeline to collect near-real-time market data.

---

<b>Visit <a href='https://heyisula.github.io/cse_unofficial_api_data_pipeline/'>this link</a> to see web view<b>

## Overview 📋

The Colombo Stock Exchange provides real-time and historical stock data via several public endpoints used by their web portal. This repository serves two purposes:
1.  **API Documentation**: Documents known endpoints, parameters, and response formats.
2.  **Data Pipeline**: A robust Python application to poll, clean, and store market data for analysis or ML applications.

---

## 🚀 Data Pipeline Features

We have built a fully automated pipeline to build your own historical dataset.

*   **Smart Polling**: Fetches data every minute (configurable) using standard HTTP requests.
*   **Session Management**: Mimics a real browser session to reliably access protected endpoints.
*   **Rate Limiting**: Respectful 0.4s delays between requests to prevent server overload.
*   **Dual Storage**:
    *   **CSV**: Appends to `data/cse_market_data.csv` for historical analysis.
    *   **JSON**: Updates `data/cse_market_snapshot.json` for real-time dashboards.

### How to Run the Pipeline

1.  **Install Dependencies**:
    ```bash
    pip install requests
    ```

2.  **Start the Collector**:
    ```bash
    python main.py
    ```
    The script will log its progress to the console and `cse_pipeline.log`.

3.  **Access Data**:
    Data is saved automatically in the `data/` directory.

---

## 🔗 API Endpoints

Base URL: `https://www.cse.lk/api/`

| Endpoint | Description | Method | Key Params |
| :--- | :--- | :--- | :--- |
| `marketStatus` | Check if market is Open/Closed | POST | - |
| `marketSummery` | Market-wide stats (ASPI, Val, Vol) | POST | - |
| `todaySharePrice` | List of all currently active stocks | POST | - |
| `companyInfoSummery` | Detailed info (Price, Vol, Cap) | POST | `symbol` |
| `tradeSummary` | Summary of trades for all securities | POST | - |
| `topGainers` | List of top gaining stocks | POST | - |
| `topLooses` | List of top losing stocks | POST | - |
| `mostActiveTrades` | Most active trades by volume | POST | - |
| `detailedTrades` | Trade-by-trade data (Heavy load) | POST | - |
| `aspiData` | All Share Price Index history | POST | - |
| `snpData` | S&P SL20 Index history | POST | - |

> **Note**: Most endpoints require a valid session cookie (JSESSIONID) or specific headers (`Origin`, `Referer`, `X-Requested-With`) to work. See `fetcher.py` for a working implementation.

visit <a href='https://github.com/heyisula/cse_unofficial_api_data_pipeline/blob/main/api_endpoint_urls.txt'>this link</a> to view all complete endpoint urls.

---

## 💻 Python Example

Here is a minimal example of how to fetch details for a single company:

```python
import requests

# 1. Setup Session (Crucial for cookies)
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 ...",
    "Origin": "https://www.cse.lk",
    "Referer": "https://www.cse.lk/",
    "X-Requested-With": "XMLHttpRequest" # Important!
})

# 2. Initialize Session
session.get("https://www.cse.lk")

# 3. Fetch Data
endpoint = "https://www.cse.lk/api/companyInfoSummery"
response = session.post(endpoint, data={"symbol": "JKH.N0000"})

print(response.json())
```

---

## Sample Response: `companyInfoSummery` 📝

```json
{
  "reqSymbolInfo": {
    "symbol": "LOLC.N0000",
    "name": "L O L C HOLDINGS PLC",
    "lastTradedPrice": 546.5,
    "change": -2.5,
    "changePercentage": -0.455,
    "marketCap": 259696800000,
    "tdyTradeVolume": 1500
  },
  "reqSymbolBetaInfo": {
    "betaValueSPSL": 1.0227
  }
}
```

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
