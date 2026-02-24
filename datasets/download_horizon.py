import urllib.request
import json
import time

planets = {
    "mercury": "199",
    "venus":   "299",
    "earth":   "399",
    "mars":    "499",
    "jupiter": "599",
    "saturn":  "699",
    "uranus":  "799",
    "neptune": "899"
}

all_data = {}

for name, id in planets.items():
    print(f"Downloading {name}...")
    url = f"https://ssd.jpl.nasa.gov/api/horizons.api?format=json&COMMAND='{id}'&OBJ_DATA='YES'&MAKE_EPHEM='NO'"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read())
            all_data[name] = data
            print(f"  {name} done")
    except Exception as e:
        print(f"  {name} failed: {e}")
    time.sleep(1)

with open('datasets/planets_horizons.json', 'w') as f:
    json.dump(all_data, f, indent=2)

print("All planets downloaded!")