from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.parse
import time

def get_distance(driver, from_address, to_address):
    base_url = "https://www.mapdevelopers.com/distance_from_to.php"
    params = {
        "from": from_address,
        "to": to_address
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    print(f"Requesting URL: {url}")
    
    driver.get(url)
    
    try:
        attempts = 0  # Initialize attempt counter
        
        while attempts < 3:  # Allow up to 3 attempts
            driving_status_element = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.ID, "driving_status"))
            )
            distance_text = driving_status_element.text
            km_distance = distance_text.split(",")[1].strip().split()[0]

            if float(km_distance) > 0:
                return float(km_distance)  # Return valid distance
            else:
                print("Driving distance is 0 km, waiting for it to update...")
                attempts += 1
                time.sleep(5)  # Wait before retrying
        
        # If all attempts fail, skip this combination
        print(f"Skipping {from_address} to {to_address} after 3 failed attempts.")
        return None

    except Exception as e:
        print(f"Could not find driving status on page: {url}, error: {e}")
        return None

# Specify the path to your ChromeDriver
chromedriver_path = ""

# Set up the Chrome WebDriver service with headless options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run browser in headless mode
chrome_options.add_argument("--disable-gpu")  # Disable GPU for headless mode
chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resources in some environments

service = Service(chromedriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # List of unique addresses
    addresses = list(set([
        'Minde allé 35',              # Godt Brød Minemyren
        'Vestre Torggaten 2',         # Godt Brød Vestre Torggaten
        'Vetrlidsallmenningen 19',    # Godt Brød Fløyen
        'Marken 1 5017',              # Godt Brød Marken
        'Nedre Korskirkeallmenningen 12',  # Godt Brød Korskirken
        'Christies gate 10 5016',          # Godt Brød Festplassen
        'Inndalsveien 6',             # Godt Brød Kronstad X og Blomsterverksted
        'Muséplassen 3',              # Godt Brød Christie
        'Damsgårdsveien 59',          # Godt Brød Fløttmannsplassen
        'Myrdalsvegen 2',             # Godt Brød Horisont
        'Lagunen Storsenter 5239'     # Lagunen
    ]))
    
    # Initialize the distance matrix with None to indicate missing values
    distance_matrix = [[None for _ in range(len(addresses))] for _ in range(len(addresses))]
    
    # Calculate distances between all combinations of addresses
    for i in range(len(addresses)):
        for j in range(len(addresses)):
            if i != j:  # Skip self-to-self distances
                from_address = addresses[i]
                to_address = addresses[j]

                # Calculate distance from i to j
                if distance_matrix[i][j] is None:  # Only calculate if not already done
                    distance = get_distance(driver, from_address, to_address)
                    if distance is not None:
                        print(f"Avstand fra {from_address} til {to_address}: {distance} km")
                        distance_matrix[i][j] = distance
                    else:
                        print(f"Kunne ikke beregne avstanden fra {from_address} til {to_address}")
                
                time.sleep(5)  # Add a delay between requests
    
    # Fill diagonal with 0 (distance from self to self)
    for i in range(len(addresses)):
        distance_matrix[i][i] = 0

    # Print the resulting matrix
    print("\nAvstandsmatrise:")
    print("     " + "     ".join(addresses))
    for i, row in enumerate(distance_matrix):
        print(f"{addresses[i]:<25} {row}")

finally:
    time.sleep(10)  # Wait before closing the browser
    driver.quit()
