import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
POLLEN_TYPES = [
    "alder_pollen",
    "birch_pollen",
    "grass_pollen",
    "mugwort_pollen",
    "olive_pollen",
    "ragweed_pollen",
]
def fetch_json(url, parameters):
    full_url = f"{url}?{urlencode(parameters)}"
    try:
        with urlopen(full_url, timeout=15) as response:
            return json.load(response)
    except HTTPError as error:
        raise RuntimeError(
            f"The server returned HTTP error {error.code}."
        ) from error
    except URLError as error:
        raise RuntimeError(
            "Could not connect to the weather service."
        ) from error
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "The weather service returned invalid data."
        ) from error
def find_city(city_name):
    parameters = {
        "name": city_name,
        "count": 1,
        "language": "en",
        "format": "json",
    }
    data = fetch_json(GEOCODING_URL, parameters)
    results = data.get("results", [])
    if not results:
        return None
    result = results[0]
    return {
        "name": result.get("name", city_name),
        "state": result.get("admin1"),
        "country": result.get("country", "Unknown country"),
        "latitude": result["latitude"],
        "longitude": result["longitude"],
    }
def get_environmental_data(latitude, longitude):
    requested_values = ["uv_index"] + POLLEN_TYPES
    parameters = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join(requested_values),
        "timezone": "auto",
    }
    data = fetch_json(AIR_QUALITY_URL, parameters)
    return {
        "time": data.get("current", {}).get("time"),
        "values": data.get("current", {}),
        "units": data.get("current_units", {}),
    }
def uv_description(uv_index):
    if uv_index is None:
        return "Unavailable"
    if uv_index < 3:
        return "Low"
    if uv_index < 6:
        return "Moderate"
    if uv_index < 8:
        return "High"
    if uv_index < 11:
        return "Very High"
    return "Extreme"
def pollen_description(value):
    """
    Pollen is reported in grains per cubic metre.
    These categories are simplified display categories rather than
    medical guidance.
    """
    if value is None:
        return "Unavailable"
    if value < 10:
        return "Low"
    if value < 50:
        return "Moderate"
    if value < 100:
        return "High"
    return "Very High"
def readable_name(variable_name):
    return variable_name.replace("_", " ").capitalize()
def display_results(location, environmental_data):
    values = environmental_data["values"]
    units = environmental_data["units"]
    location_parts = [location["name"]]
    if location["state"]:
        location_parts.append(location["state"])
    location_parts.append(location["country"])
    location_text = ", ".join(location_parts)
    print("\n" + "=" * 55)
    print(f"Environmental conditions for {location_text}")
    print(f"Coordinates: {location['latitude']}, {location['longitude']}")
    if environmental_data["time"]:
        print(f"Data time: {environmental_data['time']}")
    print("=" * 55)
    uv_index = values.get("uv_index")
    uv_unit = units.get("uv_index", "")
    print("\nUV INDEX")
    if uv_index is None:
        print("UV data is unavailable.")
    else:
        print(f"Current UV index: {uv_index} {uv_unit}".strip())
        print(f"Risk level: {uv_description(uv_index)}")
    print("\nPollen Levels")
    available_pollen = False
    for pollen_type in POLLEN_TYPES:
        value = values.get(pollen_type)
        if value is not None:
            available_pollen = True
            unit = units.get(pollen_type, "grains/m³")
            description = pollen_description(value)
            print(
                f"{readable_name(pollen_type):16} "
                f"{value} {unit} — {description}"
            )
    if not available_pollen:
        print("Pollen data is unavailable for this location.")
    print("=" * 55)
def main():
    print("Pollen and UV Tracker")
    print("Please type 'quit' to close the program.")
    while True:
        city_name = input("\nEnter city name: ").strip()
        if city_name.lower() in {"quit", "exit", "q"}:
            print("See you soon!")
            break
        if not city_name:
            print("Please enter a city name.")
            continue
        try:
            location = find_city(city_name)
            if location is None:
                print(f'No city named "{city_name}" was found.')
                continue
            environmental_data = get_environmental_data(
                location["latitude"],
                location["longitude"],
            )
            display_results(location, environmental_data)
        except RuntimeError as error:
            print(f"Error: {error}")
if __name__ == "__main__":
    main()
