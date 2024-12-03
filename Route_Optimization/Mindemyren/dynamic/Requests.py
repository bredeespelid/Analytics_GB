import requests
from itertools import product
import json

def batch_addresses(addresses, batch_size):
    """
    Splits a list of addresses into smaller batches.
    :param addresses: List of addresses.
    :param batch_size: Maximum batch size.
    :return: List of address batches.
    """
    for i in range(0, len(addresses), batch_size):
        yield addresses[i:i + batch_size]

def get_distance_matrix(api_key, origins, destinations, mode="driving", units="metric", departure_time="now"):
    base_url = "https://api.distancematrix.ai/maps/api/distancematrix/json"
    params = {
        "origins": "|".join(origins),
        "destinations": "|".join(destinations),
        "mode": mode,
        "units": units,
        "departure_time": departure_time,
        "key": api_key,
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

# Full address list
addresses = [
    "Minde allé 35, Bergen, Norway",
    "Vestre Torggaten 2, Bergen, Norway",
    "Vetrlidsallmenningen 19, Bergen, Norway",
    "Marken 1 5017, Bergen, Norway",
    "Nedre Korskirkeallmenningen 12, Bergen, Norway",
    "Christies gate 10 5016, Bergen, Norway",
    "Inndalsveien 6, Bergen, Norway",
    "Muséplassen 3, Bergen, Norway",
    "Damsgårdsveien 59, Bergen, Norway",
    "Myrdalsvegen 2, Bergen, Norway",
    "Lagunen Storsenter 5239, Bergen, Norway"
]

# API key
API_KEY = "API_KEY"

# Max number of elements allowed per request
MAX_ELEMENTS = 100

# Calculate batch size
batch_size = MAX_ELEMENTS // len(addresses)

# Create address batches
batches = list(batch_addresses(addresses, batch_size))

# Store results
results_json = []

# Process batches
try:
    for origin_batch in batches:
        for destination_batch in batches:
            response = get_distance_matrix(API_KEY, origin_batch, destination_batch, mode="driving", units="metric", departure_time="now")

            # Extract relevant data
            for i, row in enumerate(response["rows"]):
                for j, element in enumerate(row["elements"]):
                    result = {
                        "origin": origin_batch[i],
                        "destination": destination_batch[j],
                        "status": element["status"]
                    }
                    if element["status"] == "OK":
                        result["duration"] = element["duration"]["text"]
                    results_json.append(result)

    # Output full JSON response
    print(json.dumps(results_json, indent=4))

except Exception as e:
    print(f"An error occurred: {e}")
