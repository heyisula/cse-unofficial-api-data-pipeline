import csv
import json
import os
import logging
from datetime import datetime

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CSEStorage:
    """
    Handles saving our hard-earned data to CSV and JSON files.
    """
    CSV_FILENAME = "cse_market_data.csv"
    JSON_FILENAME = "cse_market_snapshot.json"
    
    # The columns we want in our CSV
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
        # Make sure the folder exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        self.csv_path = os.path.join(self.output_dir, self.CSV_FILENAME)
        self.json_path = os.path.join(self.output_dir, self.JSON_FILENAME)
        
        self._initialize_csv()

    def _initialize_csv(self):
        """Creates the CSV file and writes the headers if it's not there yet."""
        if not os.path.exists(self.csv_path):
            try:
                with open(self.csv_path, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(self.CSV_HEADERS)
                logger.info(f"Started a new CSV file at: {self.csv_path}")
            except IOError as e:
                logger.error(f"Trouble creating CSV file: {e}")

    def save_snapshot(self, market_summary, company_data_list):
        """
        Saves the current batch of data.
        1. Appends to the big CSV history.
        2. Overwrites the JSON snapshot with the latest info.
        
        Args:
            market_summary: The overall market stats (ASPI, etc).
            company_data_list: The list of raw company data we fetched.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Try to pull out the market numbers. If they aren't there, we just use None.
        aspi_value = market_summary.get('reqMarketSummery', {}).get('aspi', {}).get('value') if market_summary else None
        snp_value = market_summary.get('reqMarketSummery', {}).get('snp', {}).get('value') if market_summary else None
        market_turnover = market_summary.get('reqMarketSummery', {}).get('turnover') if market_summary else None
        
        csv_rows = []
        clean_data_list = []

        for company in company_data_list:
             # The data is usually nested in 'reqSymbolInfo'
             info = company.get('reqSymbolInfo', {})
             if not info:
                 continue

             symbol = info.get('symbol')
             name = info.get('name')
             last_price = info.get('lastTradedPrice')
             change = info.get('change')
             change_percentage = info.get('changePercentage')
             trade_volume = info.get('tdyTradeVolume') 
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
             
             # Keep a clean version for JSON
             clean_data = {
                 "timestamp": timestamp,
                 "symbol": symbol,
                 "data": info
             }
             clean_data_list.append(clean_data)

        # Write the rows to CSV
        if csv_rows:
            try:
                with open(self.csv_path, mode='a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(csv_rows)
                logger.info(f"Added {len(csv_rows)} rows to {self.csv_path}")
            except IOError as e:
                logger.error(f"Failed to append to CSV: {e}")
        else:
            logger.warning("Didn't find any data to save to CSV.")

        # Update the JSON snapshot
        try:
            snapshot = {
                "timestamp": timestamp,
                "market_summary": market_summary,
                "companies": clean_data_list
            }
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, indent=4)
            logger.info(f"Updated snapshot at {self.json_path}")
        except IOError as e:
            logger.error(f"Failed to save JSON: {e}")

if __name__ == "__main__":
    # verification
    storage = CSEStorage()
    
    # Mock data
    mock_market = {'reqMarketSummery': {'aspi': {'value': 12000}}}
    mock_company = [{'reqSymbolInfo': {'symbol': 'TEST', 'name': 'Test Co', 'lastTradedPrice': 100}}]
    
    storage.save_snapshot(mock_market, mock_company)
