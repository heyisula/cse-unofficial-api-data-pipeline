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
        "share_volume",
        "trade_count",
        "stock_turnover",
        "market_cap",
        "is_gainer",
        "is_loser",
        "is_active",
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

    def save_snapshot(self, market_summary, company_data_list, movers=None, all_sectors=None, detailed_trades=None):
        """
        Saves the current batch of data.
        1. Appends to the big CSV history.
        2. Overwrites the JSON snapshot with the latest info.
        
        Args:
            market_summary: The overall market stats (ASPI, etc).
            company_data_list: The list of raw company data we fetched.
            movers: Dict containing gainers, losers, and most active lists.
            all_sectors: List of sector index data.
            detailed_trades: All recent trades from the market.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare mover sets for quick lookup
        gainer_symbols = {item.get('symbol') for item in movers.get('gainers', [])} if movers and movers.get('gainers') else set()
        loser_symbols = {item.get('symbol') for item in movers.get('losers', [])} if movers and movers.get('losers') else set()
        active_symbols = {item.get('symbol') for item in movers.get('active', [])} if movers and movers.get('active') else set()

        # Group detailed trades by symbol for easy attachment
        trades_by_symbol = {}
        if detailed_trades and isinstance(detailed_trades.get('reqDetailTrades'), list):
            for trade in detailed_trades['reqDetailTrades']:
                sym = trade.get('symbol')
                if sym:
                    if sym not in trades_by_symbol:
                        trades_by_symbol[sym] = []
                    trades_by_symbol[sym].append(trade)

        # Try to pull out the market numbers. We handle all formats (live, fallback, augmented).
        if not market_summary:
            aspi_value = snp_value = market_turnover = None
        else:
            # We look everywhere: root level, inside reqMarketSummery, and under all known keys.
            ms = market_summary.get('reqMarketSummery', {}) if isinstance(market_summary.get('reqMarketSummery'), dict) else {}
            
            # 1. ASPI
            aspi_value = (
                market_summary.get('asi') or 
                market_summary.get('aspi', {}).get('value') or 
                ms.get('aspi', {}).get('value') or
                ms.get('asi')
            )
            
            # 2. SNP SL20
            snp_value = (
                market_summary.get('spp') or 
                market_summary.get('spt') or 
                market_summary.get('snp', {}).get('value') or
                ms.get('snp', {}).get('value') or
                ms.get('spp') or 
                ms.get('spt')
            )
            
            # 3. Turnover
            market_turnover = (
                market_summary.get('marketTurnover') or 
                market_summary.get('turnover') or 
                market_summary.get('tradeVolume') or
                ms.get('marketTurnover') or 
                ms.get('turnover') or
                ms.get('tradeVolume')
            )
        
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
             share_volume = info.get('tdyShareVolume')
             trade_count = info.get('tdyTradeVolume')
             stock_turnover = info.get('tdyTurnover')
             market_cap_val = info.get('marketCap')

             is_gainer = 1 if symbol in gainer_symbols else 0
             is_loser = 1 if symbol in loser_symbols else 0
             is_active = 1 if symbol in active_symbols else 0

             row = [
                 timestamp,
                 symbol,
                 name,
                 last_price,
                 change,
                 change_percentage,
                 share_volume,
                 trade_count,
                 stock_turnover,
                 market_cap_val,
                 is_gainer,
                 is_loser,
                 is_active,
                 aspi_value,
                 snp_value,
                 market_turnover
             ]
             csv_rows.append(row)
             
             # Keep a clean version for JSON
             clean_data = {
                 "timestamp": timestamp,
                 "symbol": symbol,
                 "data": info,
                 "flags": {
                     "is_gainer": bool(is_gainer),
                     "is_loser": bool(is_loser),
                     "is_active": bool(is_active)
                 },
                 "recent_trades": trades_by_symbol.get(symbol, [])
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
                "movers": movers,
                "sectors": all_sectors,
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
