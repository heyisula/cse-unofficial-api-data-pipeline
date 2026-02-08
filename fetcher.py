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
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error {e.response.status_code} for {endpoint}: {e.response.text}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Connection error for {endpoint}: {e}")
            return None
        except ValueError as e: 
            logger.error(f"Bad JSON from {endpoint}: {e}")
            return None

    def get_market_status(self):
        """Is the market open?"""
        return self._post("marketStatus")

    def get_market_summary(self):
        """Get the big picture stats (ASPI, S&P SL20, etc)."""
        return self._post("marketSummery")

    def get_active_symbols(self):
        """
        Grab the list of all stocks that are currently trading.
        """
        data = self._post("todaySharePrice")
        
        symbols = []
        # The API is a bit inconsistent, sometimes it's a list, sometimes a dict
        if isinstance(data, list):
             for item in data:
                symbol = item.get('symbol')
                if symbol:
                    symbols.append(symbol)
        elif isinstance(data, dict) and 'reqTodaySharePrice' in data:
             for item in data['reqTodaySharePrice']:
                symbol = item.get('symbol')
                if symbol:
                    symbols.append(symbol)
        else:
             logger.warning(f"Weird data format for todaySharePrice: {type(data)}")
             return []
        
        logger.info(f"Found {len(symbols)} active symbols.")
        return symbols

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
