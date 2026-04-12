import requests
import time
import json
import os
import pandas as pd

CACHE_FILE = "../data/geo_cache.json"

# --- ŁADOWANIE CACHE ---
def load_cache():
    full = os.path.join(os.path.dirname(__file__), CACHE_FILE)
    if os.path.exists(full):
        with open(full, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

# --- ZAPIS CACHE ---
def save_cache(cache):
    full = os.path.join(os.path.dirname(__file__), CACHE_FILE)
    with open(full, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def geocode_location(gmina, powiat, wojewodztwo):
    cache = load_cache()

    key = f"{gmina}|{powiat}|{wojewodztwo}"

    # --- jeśli już mamy w cache ---
    if key in cache:
        return cache[key]["lat"], cache[key]["lon"]

    # --- budujemy adres ---
    address = f"{gmina}, {powiat}, {wojewodztwo}, Polska"

    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}

    # --- retry 3 razy ---
    for attempt in range(3):
        try:
            response = requests.get(
                url,
                params=params,
                headers={"User-Agent": "tickets-gps"},
                timeout=10
            )
            data = response.json()

            if not data:
                cache[key] = {"lat": None, "lon": None}
                save_cache(cache)
                return None, None

            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])

            cache[key] = {"lat": lat, "lon": lon}
            save_cache(cache)

            time.sleep(1)  # limit API
            return lat, lon

        except Exception:
            time.sleep(2)

    # --- po 3 nieudanych próbach ---
    cache[key] = {"lat": None, "lon": None}
    save_cache(cache)
    return None, None
