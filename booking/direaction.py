import requests
from django.conf import settings

api_key = settings.GOOGLEMAP


def getdiractioninfo(pickup_lat,pickup_lng,drop_lat,drop_lng):
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{pickup_lat},{pickup_lng}",
        "destination": f"{drop_lat},{drop_lng}",
        "mode": "driving",
        "avoid": "tolls",
        "key": api_key,
    }
    response = requests.get(url, params=params)
    data = response.json()
    if data.get("status") != "OK":
        raise Exception(f"Google Directions API error: {data.get('status')}")
    
    route = data["routes"][0]
    leg = route["legs"][0]

    return {
        "overview_polyline": route["overview_polyline"]["points"],
        "distance_meter": leg["distance"]["value"],
        "duration_second": leg["duration"]["value"],
    }
    