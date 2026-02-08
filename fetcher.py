import requests
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CSEFetcher:
    """
    Unofficial Client for the Colombo Stock Exchange (CSE) API.
    Handles session management, rate limiting, and data retrieval.
    """
    BASE_URL = "https://www.cse.lk"
    API_URL = "https://www.cse.lk/api"
    
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
        """Visit the homepage to get valid cookies (JSESSIONID, etc.)."""
        try:
            logger.info("Initializing session...")
            self.session.get(self.BASE_URL, timeout=10)
            logger.info("Session initialized.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error initializing session: {e}")

    def _post(self, endpoint, data=None):
        """Helper method to send POST requests with error handling."""
        url = f"{self.API_URL}/{endpoint}"
        try:
            response = self.session.post(url, data=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error {e.response.status_code} fetching {endpoint}: {e.response.text}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {endpoint}: {e}")
            return None
        except ValueError as e: # JSONDecodeError
            logger.error(f"JSON Decode Error for {endpoint}: {e}")
            return None

    def get_market_status(self):
        """Check if market is open or closed."""
        return self._post("marketStatus")

    def get_market_summary(self):
        """Get high-level market statistics."""
        return self._post("marketSummery")

    def get_active_symbols(self):
        """
        Get a list of all active symbol strings from 'todaySharePrice'.
        """
        data = self._post("todaySharePrice")
        
        symbols = []
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
             logger.warning(f"Unexpected data format for todaySharePrice: {type(data)}")
             return []
        
        logger.info(f"Found {len(symbols)} active symbols.")
        return symbols

    def get_company_info(self, symbol):
        """
        Get detailed info for a company with strict rate limiting.
        """
        if not symbol:
            return None
        
        # Rate limiting: Sleep 0.4s to be safe and respectful
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
