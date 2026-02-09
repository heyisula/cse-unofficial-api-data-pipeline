"""
CSE Pipeline Configuration

Centralized configuration for the near-real-time market data pipeline.
All timing, storage, and endpoint settings are defined here.
"""

from datetime import timedelta

# ============================================================================
# POLLING SETTINGS
# ============================================================================
# Near-real-time polling interval (seconds)
# Recommended: 60 seconds (1 minute) for near-real-time updates
POLL_INTERVAL_SECONDS = 60

# Delay before retrying after an error (seconds)
RETRY_DELAY_SECONDS = 60

# ============================================================================
# MARKET HOURS (Sri Lanka Standard Time, UTC+5:30)
# ============================================================================
# Standard CSE trading hours: 09:00 - 14:30
# We add a small buffer to catch pre-open and post-close movements
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 0
MARKET_CLOSE_HOUR = 14
MARKET_CLOSE_MINUTE = 35  # 5-minute buffer after official close

# ============================================================================
# STORAGE SETTINGS
# ============================================================================
# Root directory for all data storage
DATA_DIR = "data"

# Subdirectory for symbol reference tables
REFERENCE_DIR = "reference"

# Enable legacy CSV storage alongside timestamped files
# Set to True to maintain backward compatibility
ENABLE_LEGACY_CSV = True

# ============================================================================
# RATE LIMITING
# ============================================================================
# Delay between general API requests (seconds)
REQUEST_DELAY_SECONDS = 0.4

# Delay between company info requests (seconds)
# This is enforced in fetcher.py to prevent rate limiting
COMPANY_INFO_DELAY_SECONDS = 0.4

# ============================================================================
# TIMEZONE
# ============================================================================
# Sri Lanka Standard Time offset
SL_TIMEZONE_OFFSET = timedelta(hours=5, minutes=30)

# ============================================================================
# APPROVED ENDPOINTS (Production-Safe)
# ============================================================================
# These endpoints are stable, publicly accessible, and don't require
# session-specific parameters or browser-only authentication
APPROVED_ENDPOINTS = [
    "marketStatus",        # Market open/close state
    "marketSummery",       # Market-level metrics
    "todaySharePrice",     # Core price dataset
    "tradeSummary",        # Volume & trade counts
    "aspiData",            # ASPI index
    "snpData",             # S&P SL20 index
    "topGainers",          # Momentum indicators
    "topLooses",           # Momentum indicators (note: CSE's spelling)
    "allSectors",          # Sector mapping
    "companyInfoSummery",  # Per-symbol metadata
]

# ============================================================================
# BLACKLISTED ENDPOINTS (DO NOT USE)
# ============================================================================
# These endpoints are protected, unstable, or require hidden parameters
# generated dynamically by frontend JavaScript. They break automation.
#
# NEVER use these endpoints, even experimentally:
#   - chartData: Requires hidden chartId and internal security IDs
#   - companyChartDataByStock: Requires unstable stockId, not symbol
#   - detailedTrades: Rate-limited, session-guarded, returns empty data
#   - mostActiveTrades: Part of protected endpoint group
#
# These failures are INTENTIONAL protections by CSE, not developer mistakes.
BLACKLISTED_ENDPOINTS = [
    "chartData",
    "companyChartDataByStock", 
    "detailedTrades",
    "mostActiveTrades",
]

# ============================================================================
# SYMBOL REFERENCE UPDATE SCHEDULE
# ============================================================================
# Time to refresh symbol reference table (HH:MM in 24-hour format)
# Recommended: Shortly after market open (09:05) to capture day's symbols
SYMBOL_REFRESH_HOUR = 9
SYMBOL_REFRESH_MINUTE = 5
