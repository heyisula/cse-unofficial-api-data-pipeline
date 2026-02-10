import time
import logging
from datetime import datetime, time as dtime
from fetcher import CSEFetcher
from storage import CSEStorage
from config import (
    POLL_INTERVAL_SECONDS,
    RETRY_DELAY_SECONDS,
    MARKET_OPEN_HOUR,
    MARKET_OPEN_MINUTE,
    MARKET_CLOSE_HOUR,
    MARKET_CLOSE_MINUTE,
    SYMBOL_REFRESH_HOUR,
    SYMBOL_REFRESH_MINUTE
)

# Setting up logging to catch everything (custom handler to ensure logs are flushed immediately)
class FlushFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        FlushFileHandler("cse_pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CSEPipeline")

def is_market_hours():
    """
    Checking if we are within the Colombo Stock Exchange trading window.
    Standard hours: 09:00 - 14:30 SLT, Monday to Friday.
    """
    now = datetime.now()
    
    # Weekend check
    if now.weekday() >= 5: 
        return False
        
    current_time = now.time()
    start_time = dtime(MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE)
    end_time = dtime(MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE)
    
    return start_time <= current_time <= end_time

def should_refresh_symbols():
    """
    Checking if it's time to refresh the symbol reference table  (happens once per day at a specific time).
    """
    now = datetime.now()
    current_time = now.time()
    refresh_time = dtime(SYMBOL_REFRESH_HOUR, SYMBOL_REFRESH_MINUTE)
    
    # Checking if we're within a 5 minute window of the refresh time
    time_diff_minutes = abs((current_time.hour * 60 + current_time.minute) - 
                            (refresh_time.hour * 60 + refresh_time.minute))
    
    return time_diff_minutes <= 5

def run_pipeline():
    """
    Main near-real-time polling loop.
    
    Behavior:
    - Polls every 60 seconds (1 minute) during market hours
    - Sleeps for 15 minutes when market is closed
    - Saves each endpoint's data to timestamped files (append-only)
    - Refreshes symbol reference table once per day at 09:05
    """
    logger.info("=" * 60)
    logger.info("CSE Near-Real-Time Market Data Pipeline")
    logger.info("=" * 60)
    logger.info(f"Poll Interval: {POLL_INTERVAL_SECONDS} seconds")
    logger.info(f"Market Hours: {MARKET_OPEN_HOUR:02d}:{MARKET_OPEN_MINUTE:02d} - "
                f"{MARKET_CLOSE_HOUR:02d}:{MARKET_CLOSE_MINUTE:02d}")
    logger.info("=" * 60)
    
    fetcher = CSEFetcher()
    storage = CSEStorage()
    
    symbol_refreshed_today = False

    while True:
        try:
            if not is_market_hours():
                logger.info("Market is currently closed. Sleeping for 15 minutes...")
                symbol_refreshed_today = False  # Reset for next trading day
                time.sleep(900)  # 15 minutes
                continue

            cycle_start = time.time()
            timestamp = storage.get_timestamp()
            
            logger.info("=" * 60)
            logger.info(f"POLL CYCLE START: {timestamp}")
            logger.info("=" * 60)

            # Keeping track of success/failure counts
            endpoints_fetched = []
            endpoints_failed = []

            # 1. Market Status
            logger.info("Fetching market status...")
            status_data = fetcher.get_market_status()
            if status_data:
                status_str = status_data.get('status', 'Unknown')
                logger.info(f"  ✓ Market Status: {status_str}")
                storage.save_endpoint_data('marketStatus', status_data, timestamp)
                endpoints_fetched.append('marketStatus')
            else:
                logger.warning("  ✗ Failed to fetch market status")
                endpoints_failed.append('marketStatus')

            # 2. Market Summary (includes ASPI and SNP)
            logger.info("Fetching market summary...")
            market_summary = fetcher.get_market_summary()
            if market_summary:
                logger.info("  ✓ Market summary received")
                storage.save_endpoint_data('marketSummery', market_summary, timestamp)
                endpoints_fetched.append('marketSummery')
            else:
                logger.warning("  ✗ Market summary unavailable")
                endpoints_failed.append('marketSummery')

            # 3. Trade Summary (for symbols)
            logger.info("Fetching trade summary...")
            trade_summary = fetcher._post('tradeSummary')
            if trade_summary:
                logger.info("  ✓ Trade summary received")
                storage.save_endpoint_data('tradeSummary', trade_summary, timestamp)
                endpoints_fetched.append('tradeSummary')
            else:
                logger.warning("  ✗ Trade summary unavailable")
                endpoints_failed.append('tradeSummary')

            # 4. Today's Share Prices
            logger.info("Fetching today's share prices...")
            share_prices = fetcher._post('todaySharePrice')
            if share_prices:
                logger.info("  ✓ Share prices received")
                storage.save_endpoint_data('todaySharePrice', share_prices, timestamp)
                endpoints_fetched.append('todaySharePrice')
            else:
                logger.warning("  ✗ Share prices unavailable")
                endpoints_failed.append('todaySharePrice')

            # 5. ASPI Data
            logger.info("Fetching ASPI index...")
            aspi_data = fetcher._post('aspiData')
            if aspi_data:
                logger.info("  ✓ ASPI data received")
                storage.save_endpoint_data('aspiData', aspi_data, timestamp)
                endpoints_fetched.append('aspiData')
            else:
                logger.warning("  ✗ ASPI data unavailable")
                endpoints_failed.append('aspiData')

            # 6. SNP Data
            logger.info("Fetching S&P SL20 index...")
            snp_data = fetcher._post('snpData')
            if snp_data:
                logger.info("  ✓ S&P SL20 data received")
                storage.save_endpoint_data('snpData', snp_data, timestamp)
                endpoints_fetched.append('snpData')
            else:
                logger.warning("  ✗ S&P SL20 data unavailable")
                endpoints_failed.append('snpData')

            # 7. All Sectors
            logger.info("Fetching sector indices...")
            all_sectors = fetcher.get_all_sectors()
            if all_sectors:
                logger.info("  ✓ Sector data received")
                storage.save_endpoint_data('allSectors', all_sectors, timestamp)
                endpoints_fetched.append('allSectors')
            else:
                logger.warning("  ✗ Sector data unavailable")
                endpoints_failed.append('allSectors')

            # 8. Top Movers (gainers and losers only)
            logger.info("Fetching top movers...")
            movers = fetcher.get_top_movers()
            if movers:
                if movers.get('gainers'):
                    logger.info(f"  ✓ Top gainers: {len(movers['gainers'])} stocks")
                    storage.save_endpoint_data('topGainers', movers['gainers'], timestamp)
                    endpoints_fetched.append('topGainers')
                
                if movers.get('losers'):
                    logger.info(f"  ✓ Top losers: {len(movers['losers'])} stocks")
                    storage.save_endpoint_data('topLooses', movers['losers'], timestamp)
                    endpoints_fetched.append('topLooses')
            else:
                logger.warning("  ✗ Movers data unavailable")
                endpoints_failed.append('topMovers')

            # 9. Symbol Reference Table (once per day)
            if should_refresh_symbols() and not symbol_refreshed_today:
                logger.info("Refreshing symbol reference table...")
                if share_prices and all_sectors:
                    storage.build_symbol_reference(share_prices, all_sectors)
                    symbol_refreshed_today = True
                    logger.info("  ✓ Symbol reference table updated")
                else:
                    logger.warning("  ✗ Cannot refresh symbols: missing data")

            # 10. Individual Company Data (for legacy CSV compatibility)
            symbols = fetcher.get_active_symbols()
            company_data_list = []
            
            if symbols:
                logger.info(f"Fetching detailed info for {len(symbols)} symbols...")
                
                for i, symbol in enumerate(symbols):
                    try:
                        if (i + 1) % 25 == 0:
                            logger.info(f"  Progress: {i + 1}/{len(symbols)} symbols...")

                        info = fetcher.get_company_info(symbol)
                        if info:
                            company_data_list.append(info)
                    except Exception as e:
                        logger.error(f"  ✗ Failed to fetch {symbol}: {e}")
                
                logger.info(f"  ✓ Retrieved info for {len(company_data_list)} symbols")
                
                # Save to legacy format if enabled
                storage.save_snapshot(market_summary, company_data_list, movers, all_sectors)
            else:
                logger.info("No active symbols found (normal during pre-open/closed)")

            # Summary
            logger.info("-" * 60)
            logger.info(f"POLL CYCLE COMPLETE")
            logger.info(f"  Successful: {len(endpoints_fetched)} endpoints")
            logger.info(f"  Failed: {len(endpoints_failed)} endpoints")
            if endpoints_failed:
                logger.warning(f"  Failed endpoints: {', '.join(endpoints_failed)}")
            logger.info("-" * 60)

            # Calculate sleep time
            elapsed = time.time() - cycle_start
            sleep_time = max(0, POLL_INTERVAL_SECONDS - elapsed)
            
            logger.info(f"Cycle duration: {elapsed:.2f}s | Sleeping for {sleep_time:.2f}s")
            logger.info("")  # Blank line for readability
            
            time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("=" * 60)
            logger.info("Pipeline stopped by user (Ctrl+C)")
            logger.info("=" * 60)
            break
        except Exception as e:
            logger.error(f"CRITICAL ERROR in pipeline loop: {e}", exc_info=True)
            logger.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
            time.sleep(RETRY_DELAY_SECONDS)

if __name__ == "__main__":
    run_pipeline()
