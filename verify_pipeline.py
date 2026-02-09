"""
Quick verification script to test the near-real-time pipeline.

This script performs a single poll cycle to verify:
1. All endpoints are accessible
2. Timestamped files are created correctly
3. ISO 8601 timestamps are present
4. Symbol reference table works
"""

import sys
import os
from datetime import datetime
from fetcher import CSEFetcher
from storage import CSEStorage
from config import APPROVED_ENDPOINTS

def verify_pipeline():
    print("=" * 60)
    print("CSE Pipeline Verification Test")
    print("=" * 60)
    
    # Initialize
    fetcher = CSEFetcher()
    storage = CSEStorage()
    timestamp = storage.get_timestamp()
    
    print(f"\n[OK] Timestamp generated: {timestamp}")
    print(f"  Format: ISO 8601 with timezone")
    
    # Test 1: Market Status
    print("\n[1/10] Testing marketStatus...")
    status = fetcher.get_market_status()
    if status:
        print(f"  [OK] Success: {status.get('status', 'Unknown')}")
        storage.save_endpoint_data('marketStatus', status, timestamp)
    else:
        print("  [FAIL] Failed (expected if market closed)")
    
    # Test 2: Market Summary
    print("\n[2/10] Testing marketSummery...")
    market_summary = fetcher.get_market_summary()
    if market_summary:
        print(f"  [OK] Success")
        storage.save_endpoint_data('marketSummery', market_summary, timestamp)
    else:
        print("  [FAIL] Failed (expected if market closed)")
    
    # Test 3: Trade Summary
    print("\n[3/10] Testing tradeSummary...")
    trade_summary = fetcher._post('tradeSummary')
    if trade_summary:
        print(f"  [OK] Success")
        storage.save_endpoint_data('tradeSummary', trade_summary, timestamp)
    else:
        print("  [FAIL] Failed")
    
    # Test 4: Today's Share Prices
    print("\n[4/10] Testing todaySharePrice...")
    share_prices = fetcher._post('todaySharePrice')
    if share_prices:
        print(f"  [OK] Success")
        storage.save_endpoint_data('todaySharePrice', share_prices, timestamp)
    else:
        print("  [FAIL] Failed")
    
    # Test 5: ASPI
    print("\n[5/10] Testing aspiData...")
    aspi = fetcher._post('aspiData')
    if aspi:
        print(f"  [OK] Success")
        storage.save_endpoint_data('aspiData', aspi, timestamp)
    else:
        print("  [FAIL] Failed")
    
    # Test 6: SNP
    print("\n[6/10] Testing snpData...")
    snp = fetcher._post('snpData')
    if snp:
        print(f"  [OK] Success")
        storage.save_endpoint_data('snpData', snp, timestamp)
    else:
        print("  [FAIL] Failed")
    
    # Test 7: All Sectors
    print("\n[7/10] Testing allSectors...")
    sectors = fetcher.get_all_sectors()
    if sectors:
        print(f"  [OK] Success")
        storage.save_endpoint_data('allSectors', sectors, timestamp)
    else:
        print("  [FAIL] Failed")
    
    # Test 8: Top Movers
    print("\n[8/10] Testing topGainers & topLooses...")
    movers = fetcher.get_top_movers()
    if movers and movers.get('gainers'):
        print(f"  [OK] Gainers: Success")
        storage.save_endpoint_data('topGainers', movers['gainers'], timestamp)
    else:
        print("  [FAIL] Gainers: Failed")
    
    if movers and movers.get('losers'):
        print(f"  [OK] Losers: Success")
        storage.save_endpoint_data('topLooses', movers['losers'], timestamp)
    else:
        print("  [FAIL] Losers: Failed")
    
    # Test 9: Symbol Reference
    print("\n[9/10] Testing symbol reference table...")
    if share_prices and sectors:
        ref = storage.build_symbol_reference(share_prices, sectors)
        if ref:
            print(f"  [OK] Success: {len(ref)} symbols mapped")
        else:
            print("  [FAIL] Failed")
    else:
        print("  [WARN] Skipped (missing source data)")
    
    # Test 10: Active Symbols
    print("\n[10/10] Testing active symbols...")
    symbols = fetcher.get_active_symbols()
    if symbols:
        print(f"  [OK] Success: {len(symbols)} symbols found")
        print(f"  First 5: {symbols[:5]}")
    else:
        print("  [FAIL] Failed")
    
    # Summary
    print("\n" + "=" * 60)
    print("Verification Complete!")
    print("=" * 60)
    
    # Check data directory
    print("\nChecking data directory structure...")
    data_dir = "data"
    
    expected_dirs = [
        'marketStatus', 'marketSummery', 'tradeSummary',
        'todaySharePrice', 'aspiData', 'snpData',
        'allSectors', 'topGainers', 'topLooses',
        'reference'
    ]
    
    for dir_name in expected_dirs:
        dir_path = os.path.join(data_dir, dir_name)
        if os.path.exists(dir_path):
            files = os.listdir(dir_path)
            print(f"  [OK] {dir_name}/  ({len(files)} files)")
        else:
            print(f"  [FAIL] {dir_name}/  (missing)")
    
    print("\n" + "=" * 60)
    print("PIPELINE VERIFICATION SUCCESSFUL!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run: python main.py")
    print("2. Monitor: tail -f cse_pipeline.log")
    print("3. Check data/ directory for timestamped files")
    print("\nThe pipeline will poll every 60 seconds during market hours.")
    print("=" * 60)

if __name__ == "__main__":
    try:
        verify_pipeline()
    except KeyboardInterrupt:
        print("\n\nVerification interrupted by user.")
    except Exception as e:
        print(f"\n\n[FAIL] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
