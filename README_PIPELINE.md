# CSE Market Data Pipeline

This project provides a Python-based pipeline to collect near-real-time market data from the Colombo Stock Exchange (CSE) using public endpoints.

## Overview

The pipeline periodically polls the CSE website for market status, summaries, and active company trading data. It mimics a standard web user session to respect the server's requirements.

### Components

-   **`fetcher.py`**: Handles all API interactions. It manages the session cookies and implements rate limiting (0.4s delay between requests) to avoid overwhelming the server.
-   **`storage.py`**: Manages data persistence. It saves:
    -   **`data/cse_market_data.csv`**: A historical record of all polls, appending new rows for each active company.
    -   **`data/cse_market_snapshot.json`**: A real-time snapshot of the latest poll cycle (useful for dashboards).
-   **`main.py`**: The main scheduler script. It runs an infinite loop that:
    1.  Checks market status.
    2.  Fetches active symbols.
    3.  Iterates through symbols to get detailed info.
    4.  Saves data to disk.
    5.  Sleeps for 5 minutes.

## How to Run

1.  **Install Dependencies**:
    You need python 3 and `requests`.
    ```bash
    pip install requests
    ```

2.  **Run the Pipeline**:
    ```bash
    python main.py
    ```

    The script will log its progress to the console and to `cse_pipeline.log`.

3.  **Check Data**:
    -   Open `data/cse_market_data.csv` to see the collected rows.
    -   Check `data/cse_market_snapshot.json` for the latest structured data.

## Data Collected

For each company, the following fields are collected:
-   `timestamp`: Time of data collection
-   `symbol`: Stock symbol (e.g., JKH.N0000)
-   `company_name`: Full company name
-   `last_price`: Last traded price
-   `change`: Price change
-   `change_percentage`: Percentage change
-   `trade_volume`: Today's trade volume
-   `market_cap`: Market capitalization
-   `aspi_value`: All Share Price Index value (at time of poll)
-   `snp_value`: S&P SL20 value (at time of poll)
-   `market_turnover`: Total market turnover

## Comparison with Official API

Due to the absence of an official public API and the presence of session-protected endpoints, near-real-time data collection was implemented via periodic polling of publicly accessible CSE market endpoints. 

**Why Polling?**
The public endpoints do not support streaming or WebSockets. Puling every 5 minutes provides a good balance between data freshness and server load.

**Why specific endpoints?**
We use `todaySharePrice` to get the list of active stocks and `companyInfoSummery` for details. Endpoints like `detailedTrades` are avoided as they are heavy and more likely to be restricted or rate-limited.
