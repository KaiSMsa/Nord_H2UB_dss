import json
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict

# Assuming the JSON result is saved in a variable named json_result
json_result = """
{"status": 0, "solution": [{"fuel": "MGO", "schedule": [{"year": "2025", "capacities": [{"capacity": 3000, "opened": true, "operating": false, "closed": false}, {"capacity": 7000, "opened": true, "operating": true, "closed": false}]}, {"year": "2030", "capacities": [{"capacity": 7000, "opened": true, "operating": true, "closed": false}]}, {"year": "2035", "capacities": [{"capacity": 7000, "opened": true, "operating": true, "closed": false}]}, {"year": "2040", "capacities": [{"capacity": 3000, "opened": true, "operating": true, "closed": false}]}, {"year": "2045", "capacities": [{"capacity": 3000, "opened": true, "operating": true, "closed": false}]}]}, {"fuel": "Liquid Hydrogen", "schedule": [{"year": "2025", "capacities": [{"capacity": 3000, "opened": true, "operating": false, "closed": false}]}, {"year": "2030", "capacities": [{"capacity": 7000, "opened": true, "operating": true, "closed": false}]}, {"year": "2035", "capacities": [{"capacity": 7000, "opened": true, "operating": true, "closed": false}]}, {"year": "2040", "capacities": [{"capacity": 7000, "opened": true, "operating": true, "closed": false}]}, {"year": "2045", "capacities": [{"capacity": 7000, "opened": true, "operating": true, "closed": false}]}]}, {"fuel": "Compressed Hydrogen", "schedule": [{"year": "2025", "capacities": []}, {"year": "2030", "capacities": []}, {"year": "2035", "capacities": []}, {"year": "2040", "capacities": []}, {"year": "2045", "capacities": []}]}, {"fuel": "Ammonia", "schedule": [{"year": "2025", "capacities": []}, {"year": "2030", "capacities": []}, {"year": "2035", 
"capacities": [{"capacity": 3000, "opened": true, "operating": false, "closed": false}]}, {"year": "2040", "capacities": [{"capacity": 7000, "opened": true, "operating": true, 
"closed": false}]}, {"year": "2045", "capacities": [{"capacity": 7000, "opened": true, "operating": true, "closed": false}]}]}, {"fuel": "Methanol", "schedule": [{"year": "2025", "capacities": []}, {"year": "2030", "capacities": []}, {"year": "2035", "capacities": []}, {"year": "2040", "capacities": []}, {"year": "2045", "capacities": []}]}, {"fuel": "LNG", "schedule": [{"year": "2025", "capacities": []}, {"year": "2030", "capacities": [{"capacity": 3000, "opened": true, "operating": false, "closed": false}]}, {"year": "2035", "capacities": [{"capacity": 7000, "opened": true, "operating": true, "closed": false}]}, {"year": "2040", "capacities": [{"capacity": 7000, "opened": true, "operating": true, "closed": false}]}, {"year": "2045", "capacities": [{"capacity": 7000, "opened": true, "operating": true, "closed": false}]}]}]}
"""

# Load the JSON data
data = json.loads(json_result)

# Prepare data structures
years = []
fuels = []
capacities = defaultdict(lambda: defaultdict(int))  # capacities[year][fuel] = capacity

# Extract data
for fuel_data in data['solution']:
    fuel = fuel_data['fuel']
    for schedule in fuel_data['schedule']:
        year = schedule['year']
        total_capacity = sum(capacity_info['capacity'] for capacity_info in schedule['capacities'])
        capacities[year][fuel] = total_capacity
        if year not in years:
            years.append(year)
        if fuel not in fuels:
            fuels.append(fuel)

# Sort years and fuels for consistent plotting
years.sort()
fuels.sort()

# Create a DataFrame for plotting
df = pd.DataFrame(index=years, columns=fuels).fillna(0)

for year in years:
    for fuel in fuels:
        df.loc[year, fuel] = capacities[year].get(fuel, 0)

# Plotting
ax = df.plot(kind='bar', stacked=True, figsize=(10, 6))

# Customization
plt.title('Capacity of Each Fuel Over Years')
plt.xlabel('Year')
plt.ylabel('Capacity')
plt.xticks(rotation=0)
plt.legend(title='Fuel', bbox_to_anchor=(1.05, 1), loc='upper left')

# Display the plot
plt.tight_layout()
plt.show()
