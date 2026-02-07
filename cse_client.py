import requests

class CSEClient:
    """
    Unofficial Client for the Colombo Stock Exchange (CSE) API.
    """
    BASE_URL = "https://www.cse.lk/api/"
    HEADERS = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def _post(self, endpoint, data=None):
        """Helper method to send POST requests."""
        url = self.BASE_URL + endpoint
        try:
            response = requests.post(url, headers=self.HEADERS, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {endpoint}: {e}")
            return None

    # --- Market Data ---
    def get_market_summary(self):
        """Get high-level market statistics."""
        return self._post("marketSummery")

    def get_daily_market_summary(self):
        """Get detailed daily market breakdown."""
        return self._post("dailyMarketSummery")

    def get_market_status(self):
        """Check if market is open or closed."""
        return self._post("marketStatus")

    def get_aspi_data(self):
        """Get All Share Price Index (ASPI) data."""
        return self._post("aspiData")

    def get_snp_data(self):
        """Get S&P SL20 Index data."""
        return self._post("snpData")

    def get_sector_indices(self):
        """Get data for all sectors."""
        return self._post("allSectors")

    # --- Company Data ---
    def get_company_info(self, symbol):
        """Get detailed info for a company (e.g., 'LOLC.N0000')."""
        return self._post("companyInfoSummery", {"symbol": symbol})

    def get_trade_summary(self):
        """Get summary of trades for all securities."""
        return self._post("tradeSummary")
    
    def get_detailed_trades(self, symbol=None):
        """Get detailed trades, optionally filtered by symbol."""
        data = {"symbol": symbol} if symbol else None
        return self._post("detailedTrades", data)

    def get_chart_data(self, symbol):
        """Get chart data for a symbol."""
        return self._post("chartData", {"symbol": symbol})

    def get_today_share_price(self):
        """Get today's share price data."""
        return self._post("todaySharePrice")

    # --- Movers ---
    def get_top_gainers(self):
        return self._post("topGainers")

    def get_top_losers(self):
        return self._post("topLooses")

    def get_most_active_trades(self):
        return self._post("mostActiveTrades")

# --- usage ---
if __name__ == "__main__":
    client = CSEClient()

    print("--- Market Status ---")
    print(client.get_market_status())

    print("\n--- ASPI Data ---")
    data = client.get_aspi_data()
    print(data)

    print("\n--- Company Info (LOLC) ---")
    lolc = client.get_company_info("LOLC.N0000")
    if lolc and 'reqSymbolInfo' in lolc:
        print(f"Name: {lolc['reqSymbolInfo'].get('name')}")
        print(f"Price: {lolc['reqSymbolInfo'].get('lastTradedPrice')}")
    else:
        print("Could not fetch company info.")
