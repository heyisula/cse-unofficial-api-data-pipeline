import sys
import os

# Ensure current directory is in path
sys.path.append(os.getcwd())

try:
    from cse_client import CSEClient
except ImportError:
    # Try adding apiweb if checking from root but file is in apiweb (though we know it's in root now)
    sys.path.append('apiweb')
    from cse_client import CSEClient

import json

client = CSEClient()
print("Calling get_chart_data...")
data = client.get_chart_data("JKH.N0000")

print(f"Data type: {type(data)}")
if data and 'reqTradeSummery' in data and 'chartData' in data['reqTradeSummery']:
    print(f"Chart data points: {len(data['reqTradeSummery']['chartData'])}")
    print("Sample point:", data['reqTradeSummery']['chartData'][0])
    print("SUCCESS: Mock data received.")
else:
    print("Failed to get data.")
