import json
import logging
from openai import AzureOpenAI
from google.colab import userdata
from math import ceil
from time import sleep

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set environment variables and create OpenAI client
client = AzureOpenAI(
    api_key=userdata.get('AZURE_OPENAI_API_KEY'),
    api_version="2023-03-15-preview",
    azure_endpoint=userdata.get('AZURE_OPENAI_ENDPOINT'),
)

# Function to parse JSON response with reparasjon
def parse_json_response(response_text):
    try:
        data = json.loads(response_text)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode Error: {e}")
        print(f"JSON Decode Error: {e}")

        # Fjern eventuelle kodeblokker hvis de finnes
        if response_text.startswith("```json") and response_text.endswith("```"):
            response_text = response_text[7:-3].strip()
            try:
                data = json.loads(response_text)
                logger.info("JSON reparert ved å fjerne kodeblokker.")
                return data
            except json.JSONDecodeError:
                logger.error("Kan ikke reparere JSON-svaret ved å fjerne kodeblokker.")

        # Fjern eventuelle kodeblokker uten 'json' spesifikasjon
        if response_text.startswith("```") and response_text.endswith("```"):
            response_text = response_text[3:-3].strip()
            try:
                data = json.loads(response_text)
                logger.info("JSON reparert ved å fjerne kodeblokker.")
                return data
            except json.JSONDecodeError:
                logger.error("Kan ikke reparere JSON-svaret ved å fjerne kodeblokker.")

        # Forsøk å fullføre JSON ved å legge til manglende krøllparenteser
        open_braces = response_text.count('{')
        close_braces = response_text.count('}')
        missing_braces = open_braces - close_braces
        if missing_braces > 0:
            response_text += '}' * missing_braces
            try:
                data = json.loads(response_text)
                logger.info("JSON reparert ved å legge til manglende krøllparenteser.")
                return data
            except json.JSONDecodeError:
                logger.error("Kan ikke reparere JSON-svaret etter å ha lagt til manglende krøllparenteser.")

        return None


# Function to process a batch
def process_batch(batch):
    batch_json = json.dumps(batch, ensure_ascii=False)
    system_message = (
        "You are an assistant trained to analyze customer feedback."
        "Classify each review into categories, including 'Positiv tilbakemelding', 'Dyre produkter', "
        "'Dårlige produkter', 'Dårlig kundeservice/opplevelse', 'Lang kø/ventetid', 'Dårlig renhold', and 'Ingen kommentar'. "
        "At least one of the categories should be 1. But only assign Annet Dårlig if all categories are 0. "
        "Assign binary values (0 or 1) for each category for each review. Exclude the original comment"
    )
    user_message = f"""
Analyser følgende data i JSON-format:
{batch_json}

Utdata må inkludere nøyaktig følgende JSON-struktur uten ekstra tekst, forklaringer eller formateringssymboler som kodeblokker. Svar kun med det komplette JSON-objektet:

[
    {{
        "Dato": "<date>",
        "Avd": "<avdeling>",
        "★": <star_rating>,
        "categories": {{
            "Positiv tilbakemelding": <0_or_1>,
            "Dyre produkter": <0_or_1>,
            "Dårlige produkter": <0_or_1>,
            "Dårlig kundeservice/opplevelse": <0_or_1>,
            "Lang kø/ventetid": <0_or_1>,
            "Dårlig renhold": <0_or_1>,
            "Ingen kommentar": <0_or_1>,
            "Annet Dårlig": <0>
        }}
    }}
]

Sørg for at JSON-responsen er komplett og gyldig.
"""

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]

    # Logg meldinger for debugging
    logger.info(f"Sending messages: {json.dumps(messages, ensure_ascii=False)}")

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Sender forespørsel til OpenAI (Attempt {attempt}/{max_retries})...")
            completion = client.chat.completions.create(
                model="gpt-4o-mini",  # Sørg for at dette er riktig modellnavn i Azure OpenAI
                messages=messages,
                temperature=0.4,
                # response_format er fjernet
            )
            response_text = completion.choices[0].message.content.strip()
            print("Svar mottatt fra OpenAI.")
            # Logg responsen for debugging
            logger.info(f"Response Text: {response_text}")
            # Prøv å parse JSON
            result = parse_json_response(response_text)
            if result:
                return result
            else:
                raise json.JSONDecodeError("Ufullstendig JSON etter reparasjon", response_text, len(response_text))
        except json.JSONDecodeError as jde:
            logger.error(f"JSON Decode Error processing batch: {str(jde)}")
            print(f"JSON Decode Error under behandling av batch: {str(jde)}")
            print("Respons fra OpenAI:")
            print(response_text)  # Skriv ut den faktiske responsen for debugging
            if attempt < max_retries:
                sleep_time = 2 ** attempt  # Eksponentiell tilbakegang
                print(f"Prøver igjen om {sleep_time} sekunder...")
                sleep(sleep_time)
            else:
                print("Maksimalt antall retries nådd. Hopper over batch.")
                return None
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
            print(f"Feil under behandling av batch: {str(e)}")
            return None

def main():
    print("Starter hovedfunksjonen")
    # Load data from JSON file
    file_path = "Google_ratings.json"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        print(f"Lastet {len(json_data)} elementer fra {file_path}")
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        print(f"Feil: Fil ikke funnet - {file_path}")
        return
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {file_path}")
        print(f"Feil: Ugyldig JSON i fil - {file_path}")
        return

    if not json_data:
        print("JSON-dataen er tom.")
        logger.warning("JSON-dataen er tom.")
        return

    # Definer batch-størrelse
    batch_size = 15  # Redusert for bedre håndtering
    total_items = len(json_data)
    total_batches = ceil(total_items / batch_size)
    print(f"Totalt antall elementer: {total_items}")
    print(f"Batch-størrelse: {batch_size}")
    print(f"Totalt antall batches: {total_batches}")
    logger.info(f"Totalt antall elementer: {total_items}")
    logger.info(f"Batch-størrelse: {batch_size}")
    logger.info(f"Totalt antall batches: {total_batches}")

    all_results = []
    # Ingen 'department_name' nødvendig siden hver element inkluderer sin egen 'Avd'

    for batch_num in range(total_batches):
        start_index = batch_num * batch_size
        end_index = min(start_index + batch_size, total_items)
        current_batch = json_data[start_index:end_index]
        print(f"Behandler batch {batch_num + 1} av {total_batches} (element {start_index} til {end_index - 1})")
        logger.info(f"Behandler batch {batch_num + 1} av {total_batches} (element {start_index} til {end_index - 1})")

        result = process_batch(current_batch)

        if result:
            # Anta at result er en liste av objekter
            all_results.extend(result)
            print(f"Batch {batch_num + 1} behandlet suksessfullt.")
            logger.info(f"Batch {batch_num + 1} behandlet suksessfullt.")
        else:
            logger.error(f"Failed to process batch {batch_num + 1}")
            print(f"Feil: Kunne ikke behandle batch {batch_num + 1}")
            # Fortsett med neste batch

        # Optional: Sleep mellom requests for å unngå rate limiting
        sleep(1)  # Juster eller fjern denne linjen basert på API-krav

    # Etter at alle batches er behandlet
    if all_results:
        logger.info("Alle batches behandlet. Samlet resultater:")
        print("Behandling fullført for alle elementer.")
        print(f"Totalt antall resultater: {len(all_results)}")

        # Lagre endelige resultater til en fil
        output_file = "Processed_Google_ratings.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)
            print(f"Resultatene er lagret til {output_file}")
            logger.info(f"Resultatene er lagret til {output_file}")
        except Exception as e:
            logger.error(f"Feil ved lagring av resultatene: {str(e)}")
            print(f"Feil: Kunne ikke lagre resultatene til {output_file}")
    else:
        logger.error("Ingen resultater ble behandlet.")
        print("Feil: Ingen resultater ble behandlet.")

    print("Alle oppgaver er ferdige.")
    logger.info("Alle oppgaver er ferdige.")

# Kall main() direkte uten sjekk for __name__
main()
