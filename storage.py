import csv
import json
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CSEStorage:
    """
    Handles storage of CSE market data to CSV and JSON files.
    """
    CSV_FILENAME = "cse_market_data.csv"
    JSON_FILENAME = "cse_market_snapshot.json"
    
    # Define CSV columns based on requirements
    CSV_HEADERS = [
        "timestamp",
        "symbol",
        "company_name",
        "last_price",
        "change",
        "change_percentage",
        "trade_volume",
        "market_cap",
        "aspi_value",
        "snp_value",
        "market_turnover"
    ]

    def __init__(self, output_dir="data"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        self.csv_path = os.path.join(self.output_dir, self.CSV_FILENAME)
        self.json_path = os.path.join(self.output_dir, self.JSON_FILENAME)
        
        self._initialize_csv()

    def _initialize_csv(self):
        """Creates the CSV file with headers if it doesn't exist."""
        if not os.path.exists(self.csv_path):
            try:
                with open(self.csv_path, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(self.CSV_HEADERS)
                logger.info(f"Created new CSV file: {self.csv_path}")
            except IOError as e:
                logger.error(f"Error creating CSV file: {e}")

    def save_snapshot(self, market_summary, company_data_list):
        """
        Saves a market snapshot (list of company data) to CSV and JSON.
        
        Args:
            market_summary: Dict containing high-level market data (status, ASPI, etc)
            company_data_list: List of dicts, where each dict is the raw response from companyInfoSummery
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Extract market-level metrics
        # Note: market_summary structure depends on the exact API response. 
        # We try to extract what we can, but fallback to 0 or None.
        aspi_value = market_summary.get('reqMarketSummery', {}).get('aspi', {}).get('value') if market_summary else None
        snp_value = market_summary.get('reqMarketSummery', {}).get('snp', {}).get('value') if market_summary else None
        market_turnover = market_summary.get('reqMarketSummery', {}).get('turnover') if market_summary else None
        
        # Prepare rows for CSV
        csv_rows = []
        clean_data_list = []

        for company in company_data_list:
             # structure: {'reqSymbolInfo': {...}, ...}
             info = company.get('reqSymbolInfo', {})
             if not info:
                 continue

             symbol = info.get('symbol')
             name = info.get('name')
             last_price = info.get('lastTradedPrice')
             change = info.get('change')
             change_percentage = info.get('changePercentage')
             trade_volume = info.get('tdyTradeVolume') # or 'tdyShareVolume'? Requirements say 'trade_volume'
             market_cap_val = info.get('marketCap')

             row = [
                 timestamp,
                 symbol,
                 name,
                 last_price,
                 change,
                 change_percentage,
                 trade_volume,
                 market_cap_val,
                 aspi_value,
                 snp_value,
                 market_turnover
             ]
             csv_rows.append(row)
             
             # Create a clean dict for JSON dump (optional, but good for snapshots)
             clean_data = {
                 "timestamp": timestamp,
                 "symbol": symbol,
                 "data": info
             }
             clean_data_list.append(clean_data)

        # Write to CSV
        if csv_rows:
            try:
                with open(self.csv_path, mode='a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(csv_rows)
                logger.info(f"Appended {len(csv_rows)} rows to {self.csv_path}")
            except IOError as e:
                logger.error(f"Error appending to CSV: {e}")
        else:
            logger.warning("No data to save to CSV.")

        # Write latest snapshot to JSON (Overwrites previous file)
        try:
            snapshot = {
                "timestamp": timestamp,
                "market_summary": market_summary,
                "companies": clean_data_list
            }
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, indent=4)
            logger.info(f"Saved snapshot to {self.json_path}")
        except IOError as e:
            logger.error(f"Error saving JSON: {e}")

if __name__ == "__main__":
    # verification
    storage = CSEStorage()
    
    # Mock data
    mock_market = {'reqMarketSummery': {'aspi': {'value': 12000}}}
    mock_company = [{'reqSymbolInfo': {'symbol': 'TEST', 'name': 'Test Co', 'lastTradedPrice': 100}}]
    
    storage.save_snapshot(mock_market, mock_company)
