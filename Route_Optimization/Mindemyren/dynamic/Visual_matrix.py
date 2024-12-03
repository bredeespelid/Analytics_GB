import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load JSON data from file
with open('/content/results.json', 'r') as file:
    trips = json.load(file)

# Define the mapping of full addresses to simplified names
address_mapping = {
    'Minde allé 35, Bergen, Norway': 'Mindemyren',
    'Vestre Torggaten 2, Bergen, Norway': 'Vestre Torggaten',
    'Vetrlidsallmenningen 19, Bergen, Norway': 'Fløyen',
    'Marken 1 5017, Bergen, Norway': 'Marken',
    'Nedre Korskirkeallmenningen 12, Bergen, Norway': 'Korskirken',
    'Christies gate 10 5016, Bergen, Norway': 'Festplassen',
    'Inndalsveien 6, Bergen, Norway': 'Kronstad',
    'Muséplassen 3, Bergen, Norway': 'Christie',
    'Damsgårdsveien 59, Bergen, Norway': 'Fløttmannsplassen',
    'Myrdalsvegen 2, Bergen, Norway': 'Horisont',
    'Lagunen Storsenter 5239, Bergen, Norway': 'Lagunen'
}

# Get unique locations using the simplified names
locations = sorted(set(address_mapping[trip["origin"]] for trip in trips if trip["origin"] in address_mapping) | 
                   set(address_mapping[trip["destination"]] for trip in trips if trip["destination"] in address_mapping))

# Initialize time matrix
time_matrix = pd.DataFrame(np.inf, index=locations, columns=locations)

# Fill the time matrix with durations
for trip in trips:
    if trip["origin"] in address_mapping and trip["destination"] in address_mapping:
        origin = address_mapping[trip["origin"]]
        destination = address_mapping[trip["destination"]]
        duration = int(trip["duration"].replace(" mins", "").replace(" min", ""))
        time_matrix.loc[origin, destination] = duration

# Ensure diagonal is zero (no time needed to travel to the same location)
np.fill_diagonal(time_matrix.values, 0)

# Display the resulting time matrix using a heatmap
plt.figure(figsize=(12, 10))
sns.heatmap(time_matrix, annot=True, cmap="YlGnBu", fmt="g")
plt.title('Time Matrix (in minutes)')
plt.ylabel('Origin')
plt.xlabel('Destination')
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()
