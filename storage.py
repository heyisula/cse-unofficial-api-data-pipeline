import csv
import json
import os
import logging
from datetime import datetime, timezone
from config import SL_TIMEZONE_OFFSET, DATA_DIR, REFERENCE_DIR, ENABLE_LEGACY_CSV

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CSEStorage:
    """
    Handles saving market data in a time series, append only structure.
    
    Storage Architecture:
    - Timestamped files per endpoint (no overwrites)
    - Optional legacy CSV for backward compatibility
    - Symbol reference table for normalization
    """
    
    # Legacy CSV settings
    CSV_FILENAME = "cse_market_data.csv"
    JSON_FILENAME = "cse_market_snapshot.json"
    
    CSV_HEADERS = [
        "timestamp",
        "symbol",
        "company_name",
        "security_type",
        "last_price",
        "change",
        "change_percentage",
        "share_volume",
        "trade_count",
        "stock_turnover",
        "market_cap",
        "is_gainer",
        "is_loser",
        "aspi_value",
        "snp_value",
        "market_turnover"
    ]

    @staticmethod
    def get_security_type(symbol):
        """
        Determine the security type from the symbol suffix.
        
        Returns:
            str: Security type classification
                - NORMAL_STOCK: Regular listed stocks (.N0000)
                - UNIT_TRUST: Investment funds (.U0000)
                - OFF_BOARD: Off-board trading (.X0000)
                - RIGHTS_ISSUE: Rights issues (.R0000)
                - OTHER: Unknown or different suffix
        """
        if not symbol:
            return 'UNKNOWN'
        
        if '.U' in symbol:
            return 'UNIT_TRUST'
        elif '.R' in symbol:
            return 'RIGHTS_ISSUE'
        elif '.X' in symbol:
            return 'OFF_BOARD'
        elif '.N' in symbol:
            return 'NORMAL_STOCK'
        else:
            return 'OTHER'

    def __init__(self, output_dir=DATA_DIR):
        self.output_dir = output_dir
        
        # Make sure the root data directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Create reference directory
        self.reference_dir = os.path.join(self.output_dir, REFERENCE_DIR)
        if not os.path.exists(self.reference_dir):
            os.makedirs(self.reference_dir)
        
        # Legacy paths
        self.csv_path = os.path.join(self.output_dir, self.CSV_FILENAME)
        self.json_path = os.path.join(self.output_dir, self.JSON_FILENAME)
        
        if ENABLE_LEGACY_CSV:
            self._initialize_csv()

    def _initialize_csv(self):
        """Creates the legacy CSV file and writes the headers if it's not there yet."""
        if not os.path.exists(self.csv_path):
            try:
                with open(self.csv_path, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(self.CSV_HEADERS)
                logger.info(f"Started a new legacy CSV file at: {self.csv_path}")
            except IOError as e:
                logger.error(f"Trouble creating CSV file: {e}")

    def get_timestamp(self):
        """
        Format: 2026-02-09T18:45:00+05:30
        """
        tz = timezone(SL_TIMEZONE_OFFSET)
        return datetime.now(tz).isoformat()

    def create_endpoint_directory(self, endpoint_name):
        """
        Create a directory for a specific endpoint if it doesn't exist.
        
        Args:
            endpoint_name: Name of the endpoint (e.g., 'todaySharePrice')
        
        Returns:
            Path to the endpoint directory
        """
        endpoint_dir = os.path.join(self.output_dir, endpoint_name)
        if not os.path.exists(endpoint_dir):
            os.makedirs(endpoint_dir)
            logger.debug(f"Created directory: {endpoint_dir}")
        return endpoint_dir

    def save_endpoint_data(self, endpoint_name, data, timestamp=None):
        """
        Save endpoint response with timestamp to a time-series file.
        Each poll creates a NEW file (append-only, no overwrites).
        
        Args:
            endpoint_name: Name of the endpoint (e.g., 'todaySharePrice')
            data: Raw API response
        
        Returns:
            Path to the saved file
        """
        if data is None:
            logger.warning(f"Skipping save for {endpoint_name}: data is None")
            return None
        
        if timestamp is None:
            timestamp = self.get_timestamp()
        
        # Create directory for this endpoint
        endpoint_dir = self.create_endpoint_directory(endpoint_name)
        
        # Generate filename: YYYY-MM-DD_HH-MM.json
        # Extract YYYY-MM-DD_HH-MM from ISO
        # 2026-02-09T18:45:00+05:30 -> 2026-02-09_18-45
        dt_str = timestamp[:16]  # 2026-02-09T18:45
        filename = dt_str.replace('T', '_').replace(':', '-') + '.json'
        filepath = os.path.join(endpoint_dir, filename)
        
        # Wrap data with metadata
        output_data = {
            'fetched_at': timestamp,
            'endpoint': endpoint_name,
            'data': data
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2)
            logger.info(f"Saved {endpoint_name} → {filename}")
            return filepath
        except IOError as e:
            logger.error(f"Failed to save {endpoint_name}: {e}")
            return None

    def build_symbol_reference(self, price_data, sectors_data):
        """
        Creating a static reference table mapping symbols to company names and sectors (once per day or on startup)
        
        Args:
            price_data: Response from todaySharePrice
            sectors_data: Response from allSectors
        
        Returns:
            Dictionary with symbol -> {company_name, sector, sector_index}
        """
        reference = {}
        
        # Extract symbol → company mapping from price data
        # Handle both wrapped and direct list formats
        if isinstance(price_data, dict):
            items = price_data.get('reqTodaySharePrice', [])
        elif isinstance(price_data, list):
            items = price_data
        else:
            logger.warning(f"Unexpected price_data format: {type(price_data)}")
            items = []
        
        for item in items:
            symbol = item.get('symbol')
            company_name = item.get('name')
            sector = item.get('sector')  # Sometimes included in price data
            
            if symbol:
                reference[symbol] = {
                    'company_name': company_name,
                    'sector': sector,
                    'sector_index': None
                }
        
        # Enhance with sector information if available
        if sectors_data:
            if isinstance(sectors_data, dict) and 'reqAllSectors' in sectors_data:
                sector_list = sectors_data['reqAllSectors']
            elif isinstance(sectors_data, list):
                sector_list = sectors_data
            else:
                sector_list = []
            
            # Build sector index mapping
            for sector in sector_list:
                sector_name = sector.get('index') or sector.get('name')
                sector_index_value = sector.get('value')
                
                # Note: Without additional symbol-to-sector mapping in the API,rely on the sector field in price_data.
        
        # Save to reference directory
        ref_path = os.path.join(self.reference_dir, "symbol_metadata.json")
        
        try:
            with open(ref_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'generated_at': self.get_timestamp(),
                    'symbol_count': len(reference),
                    'symbols': reference
                }, f, indent=2)
            
            logger.info(f"Symbol reference table saved with {len(reference)} symbols")
            return reference
        except IOError as e:
            logger.error(f"Failed to save symbol reference: {e}")
            return None

    def save_snapshot(self, market_summary, company_data_list, movers=None, all_sectors=None):
        """
        Saves data in time-series format AND optionally to legacy CSV.
        
        Args:
            market_summary: The overall market stats (ASPI, etc)
            company_data_list: List of company data from companyInfoSummery
            movers: Dict containing gainers and losers
            all_sectors: List of sector index data
        """
        timestamp = self.get_timestamp()
        
        # Save each endpoint's data to its own timestamped file
        if market_summary:
            self.save_endpoint_data('marketSummery', market_summary, timestamp)
        
        if company_data_list:
            # Wrap company list in the expected format
            self.save_endpoint_data('companyData', company_data_list, timestamp)
        
        if movers:
            if movers.get('gainers'):
                self.save_endpoint_data('topGainers', movers['gainers'], timestamp)
            if movers.get('losers'):
                self.save_endpoint_data('topLooses', movers['losers'], timestamp)
        
        if all_sectors:
            self.save_endpoint_data('allSectors', all_sectors, timestamp)
        
        # Legacy CSV and JSON snapshot
        if ENABLE_LEGACY_CSV:
            self._save_legacy_formats(timestamp, market_summary, company_data_list, movers, all_sectors)

    def _save_legacy_formats(self, timestamp, market_summary, company_data_list, movers, all_sectors):
        """
        Save data in the old CSV + JSON snapshot format for backward compatibility.
        """
        # Prepare mover sets for quick lookup
        gainer_symbols = set()
        loser_symbols = set()
        
        if movers:
            if movers.get('gainers'):
                gainer_symbols = {item.get('symbol') for item in movers['gainers'] if item.get('symbol')}
            if movers.get('losers'):
                loser_symbols = {item.get('symbol') for item in movers['losers'] if item.get('symbol')}
        
        # Extract market-level values
        # Initialize with 0.0 (Filling missing values with 0)
        aspi_value = 0.0
        snp_value = 0.0
        market_turnover = 0.0
        
        if market_summary:
            # The CSE API returns values directly in the top level dict or sometimes in reqMarketSummery
            ms = market_summary.get('reqMarketSummery', {}) if isinstance(market_summary.get('reqMarketSummery'), dict) else {}
            
            # 1. ASPI Value
            aspi_value = (
                market_summary.get('aspi', {}).get('value') or 
                market_summary.get('asi') or 
                ms.get('aspi', {}).get('value') or
                ms.get('asi') or
                0.0
            )
            
            # 2. SNP Value
            snp_value = (
                market_summary.get('snp', {}).get('value') or 
                market_summary.get('spp') or 
                market_summary.get('spt') or 
                ms.get('snp', {}).get('value') or
                ms.get('spp') or 
                ms.get('spt') or
                0.0
            )
            
            # 3. Market Turnover
            market_turnover = (
                market_summary.get('tradeVolume') or 
                market_summary.get('marketTurnover') or 
                market_summary.get('turnover') or 
                ms.get('tradeVolume') or
                ms.get('marketTurnover') or 
                ms.get('turnover') or
                0.0
            )
        
        csv_rows = []
        clean_data_list = []

        for company in company_data_list:
            info = company.get('reqSymbolInfo', {})
            if not info:
                continue

            symbol = info.get('symbol')
            name = info.get('name')
            security_type = self.get_security_type(symbol)
            last_price = info.get('lastTradedPrice')
            change = info.get('change')
            change_percentage = info.get('changePercentage')
            share_volume = info.get('tdyShareVolume')
            
            #Filling missing values with 0 for better data handling
            trade_count = info.get('tdyTradeVolume') or 0
            stock_turnover = info.get('tdyTurnover') or 0.0
            market_cap_val = info.get('marketCap') or 0.0

            is_gainer = 1 if symbol in gainer_symbols else 0
            is_loser = 1 if symbol in loser_symbols else 0

            row = [
                timestamp,
                symbol,
                name,
                security_type,
                last_price,
                change,
                change_percentage,
                share_volume,
                trade_count,
                stock_turnover,
                market_cap_val,
                is_gainer,
                is_loser,
                aspi_value,
                snp_value,
                market_turnover
            ]
            csv_rows.append(row)
            
            clean_data = {
                "timestamp": timestamp,
                "symbol": symbol,
                "data": info,
                "flags": {
                    "is_gainer": bool(is_gainer),
                    "is_loser": bool(is_loser)
                }
            }
            clean_data_list.append(clean_data)

        # Write to CSV
        if csv_rows:
            try:
                with open(self.csv_path, mode='a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(csv_rows)
                logger.info(f"Added {len(csv_rows)} rows to legacy CSV")
            except IOError as e:
                logger.error(f"Failed to append to CSV: {e}")

        # Update JSON snapshot
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
            logger.info(f"Updated legacy JSON snapshot")
        except IOError as e:
            logger.error(f"Failed to save JSON: {e}")


if __name__ == "__main__":
    # Verification
    storage = CSEStorage()
    
    # Test timestamped storage
    mock_market = {'reqMarketSummery': {'aspi': {'value': 12000}}}
    mock_company = [{'reqSymbolInfo': {'symbol': 'TEST', 'name': 'Test Co', 'lastTradedPrice': 100}}]
    
    print("Testing time-series storage...")
    storage.save_endpoint_data('testEndpoint', {'test': 'data'})
    
    print("\nTesting snapshot save...")
    storage.save_snapshot(mock_market, mock_company)
    
    print("\nDone. Check the data/ directory for timestamped files.")
