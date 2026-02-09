import requests
import time
import logging

# Set up logging so we can see what's happening
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CSEFetcher:
    """
    Client for collecting data from the Colombo Stock Exchange (CSE).
    It manages the connection, cookies, and makes sure we don't hit the server too hard.
    """
    BASE_URL = "https://www.cse.lk"
    API_URL = "https://www.cse.lk/api"
    
    # We need to look like a real browser to get the data
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://www.cse.lk",
        "Referer": "https://www.cse.lk/",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self._initialize_session()

    def _initialize_session(self):
        """Go to the homepage first to grab the necessary cookies."""
        try:
            logger.info("Starting up session...")
            self.session.get(self.BASE_URL, timeout=10)
            logger.info("Session ready.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Couldn't start session: {e}")

    def _post(self, endpoint, data=None):
        """Send a POST request to the API."""
        url = f"{self.API_URL}/{endpoint}"
        try:
            response = self.session.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            # Handle 204 No Content or empty bodies gracefully
            if response.status_code == 204 or not response.text.strip():
                return None
                
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error {e.response.status_code} for {endpoint}: {e.response.text}")
            return None
        except (requests.exceptions.JSONDecodeError, ValueError) as e:
            # During certain market phases (like pre-open), some endpoints might return 
            # non-JSON or weirdly formatted empty responses.
            logger.debug(f"Could not parse JSON from {endpoint}. Market might be in transition.")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Connection error for {endpoint}: {e}")
            return None

    def get_market_status(self):
        """Is the market open?"""
        return self._post("marketStatus")

    def get_market_summary(self):
        """Get the big picture stats (ASPI, S&P SL20, etc)."""
        data = self._post("marketSummery")
        
        # If we got a basic summary, try to augment it with current index values
        if isinstance(data, dict):
            # Fetch ASPI and SNP separately since marketSummery often lacks them
            aspi_data = self._post("aspiData")
            if aspi_data:
                data['aspi'] = aspi_data
            
            snp_data = self._post("snpData")
            if snp_data:
                data['snp'] = snp_data
            
            return data
            
        # Fallback to dailyMarketSummery if marketSummery is empty (common in pre-open)
        logger.info("Market summary empty, trying dailyMarketSummery fallback...")
        daily_data = self._post("dailyMarketSummery")
        if daily_data and isinstance(daily_data, list) and len(daily_data) > 0:
            # Return the most recent record
            return daily_data[0][0] if isinstance(daily_data[0], list) else daily_data[0]
            
        return None

    def get_active_symbols(self):
        """
        Grab the list of all symbols that are or were recently active.
        We've switched this to 'tradeSummary' because 'todaySharePrice' 
        often limits results to just 10 items.
        """
        data = self._post("tradeSummary")
        
        symbols = []
        # Support both the expected 'reqTradeSummery' wrapper and direct list fallback
        if isinstance(data, dict) and 'reqTradeSummery' in data:
            items = data['reqTradeSummery']
        elif isinstance(data, list):
            items = data
        else:
            logger.warning(f"Unexpected data format for tradeSummary: {type(data)}")
            # Try todaySharePrice as a last resort backup
            logger.info("Trying todaySharePrice as backup...")
            data = self._post("todaySharePrice")
            items = data if isinstance(data, list) else data.get('reqTodaySharePrice', []) if isinstance(data, dict) else []

        if not items:
            logger.warning("No symbols found in tradeSummary or backup.")
            return []

        symbols = set()
        for item in items:
            symbol = item.get('symbol')
            if symbol:
                symbols.add(symbol)
        
        symbols_list = sorted(list(symbols))
        logger.info(f"Retrieved {len(symbols_list)} unique symbols from market.")
        return symbols_list


    def get_company_info(self, symbol):
        """
        Get the details for a specific company.
        We pause a bit here to be nice to the server.
        """
        if not symbol:
            return None
        
        # Take a breath properly so we don't get blocked
        time.sleep(0.4) 
        
        return self._post("companyInfoSummery", {"symbol": symbol.upper()})

    def get_all_sectors(self):
        """Get index data for all industry sectors."""
        return self._post("allSectors")

    def get_top_movers(self):
        """
        Fetch market movers (top gainers and losers).
        Returns a dict with gainers and losers.
        
        Note: 'mostActiveTrades' endpoint is blacklisted (session-protected)
        and has been removed to ensure pipeline stability.
        """
        return {
            "gainers": self._post("topGainers"),
            "losers": self._post("topLooses")
        }


if __name__ == "__main__":
    # verification
    fetcher = CSEFetcher()
    status = fetcher.get_market_status()
    print(f"Market Status: {status}")
    
    symbols = fetcher.get_active_symbols()
    if symbols:
        print(f"First 5 symbols: {symbols[:5]}")
        print(f"Fetching info for {symbols[0]}...")
        info = fetcher.get_company_info(symbols[0])
        print(info)
