import time
import logging
from datetime import datetime
from fetcher import CSEFetcher
from storage import CSEStorage

# Set up logging to catch everything
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cse_pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CSEPipeline")

POLL_INTERVAL_SECONDS = 60  # Check every minute

def run_pipeline():
    logger.info("Firing up the CSE Market Data Pipeline...")
    fetcher = CSEFetcher()
    storage = CSEStorage()

    while True:
        try:
            start_time = time.time()
            logger.info("--------------------------------------------------")
            logger.info("Starting a new poll cycle...")

            # 1. Is the market open?
            status_data = fetcher.get_market_status()
            status_str = status_data.get('marketStatus', 'Unknown') if status_data else 'Unknown'
            logger.info(f"Market Status: {status_str}")

            # Even if it's closed, we'll carry on for now, just in case.
            
            # 2. Get the big picture
            market_summary = fetcher.get_market_summary()
            if not market_summary:
                logger.error("Couldn't get market summary. Skipping this round.")
            
            # 3. Who's trading?
            symbols = fetcher.get_active_symbols()
            if not symbols:
                logger.warning("No active symbols found. Nothing to fetch.")
            else:
                logger.info(f"Fetching details for {len(symbols)} symbols...")
                
                company_data_list = []
                for i, symbol in enumerate(symbols):
                    try:
                        # Print a little update every 10 symbols so we know it's alive
                        if (i + 1) % 10 == 0:
                            logger.info(f"Processed {i + 1}/{len(symbols)} symbols...")

                        info = fetcher.get_company_info(symbol)
                        if info:
                            company_data_list.append(info)
                    except Exception as e:
                        logger.error(f"Oops, failed to fetch info for {symbol}: {e}")
                        # Keep going, one failure shouldn't stop the train
                
                # 4. Save what we got
                if company_data_list:
                    storage.save_snapshot(market_summary, company_data_list)
                    logger.info("Saved data to disk.")
                else:
                    logger.warning("No data to save this time.")

            # 5. Wait for the next round
            elapsed = time.time() - start_time
            sleep_time = max(0, POLL_INTERVAL_SECONDS - elapsed)
            logger.info(f"Cycle done in {elapsed:.2f} seconds. Resting for {sleep_time:.2f} seconds...")
            
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
