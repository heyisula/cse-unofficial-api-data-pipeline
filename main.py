import time
import logging
from datetime import datetime
from fetcher import CSEFetcher
from storage import CSEStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cse_pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CSEPipeline")

POLL_INTERVAL_SECONDS = 60  # 1 minute

def run_pipeline():
    logger.info("Starting CSE Market Data Pipeline...")
    fetcher = CSEFetcher()
    storage = CSEStorage()

    while True:
        try:
            start_time = time.time()
            logger.info("--------------------------------------------------")
            logger.info("Starting new poll cycle...")

            # 1. Check Market Status
            status_data = fetcher.get_market_status()
            status_str = status_data.get('marketStatus', 'Unknown') if status_data else 'Unknown'
            logger.info(f"Market Status: {status_str}")

            # If market is closed, we might still want to run once to capture closing data, 
            # but usually we want to keep running to catch the opening. 
            # For now, we proceed regardless of status, but you could add logic to sleep longer if closed.
            
            # 2. Get Market Summary
            market_summary = fetcher.get_market_summary()
            if not market_summary:
                logger.error("Failed to get market summary. Skipping this cycle.")
            
            # 3. Get Active Symbols
            symbols = fetcher.get_active_symbols()
            if not symbols:
                logger.warning("No active symbols found. Skipping symbol details.")
            else:
                logger.info(f"Fetching data for {len(symbols)} symbols...")
                
                company_data_list = []
                for i, symbol in enumerate(symbols):
                    try:
                        # Log progress every 10 symbols
                        if (i + 1) % 10 == 0:
                            logger.info(f"Processed {i + 1}/{len(symbols)} symbols...")

                        info = fetcher.get_company_info(symbol)
                        if info:
                            company_data_list.append(info)
                    except Exception as e:
                        logger.error(f"Error fetching info for {symbol}: {e}")
                        # Continue to next symbol even if one fails
                
                # 4. Save Data
                if company_data_list:
                    storage.save_snapshot(market_summary, company_data_list)
                    logger.info("Data saved successfully.")
                else:
                    logger.warning("No company data collected to save.")

            # 5. Sleep until next cycle
            elapsed = time.time() - start_time
            sleep_time = max(0, POLL_INTERVAL_SECONDS - elapsed)
            logger.info(f"Cycle completed in {elapsed:.2f} seconds. Sleeping for {sleep_time:.2f} seconds...")
            
            time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("Pipeline stopped by user.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in pipeline loop: {e}", exc_info=True)
            # Sleep a bit before retrying to avoid rapid error loops
            time.sleep(60)

if __name__ == "__main__":
    run_pipeline()
