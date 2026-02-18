import requests
from django.conf import settings
from .models import BouncieToken

BASE_URL = "https://api.bouncie.dev/v1"


class BouncieNotAuthorized(Exception):
    """Raised when no valid Bouncie token exists."""
    pass


class BouncieAPIError(Exception):
    """Raised when the Bouncie API returns an error response."""
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Bouncie API {status_code}: {detail}")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_headers():
    """
    Returns auth headers for Bouncie API, auto-refreshing the token if expired.
    Raises BouncieNotAuthorized if admin has never authorised.
    """
    token = BouncieToken.get_valid_token()
    if token is None:
        raise BouncieNotAuthorized(
            "Bouncie is not connected. An admin must complete the OAuth2 authorization first."
        )
    return {
        "Authorization": token.access_token,
        "Content-Type": "application/json",
    }


def _get(path, params=None):
    """
    Makes a GET request to the Bouncie API.
    Returns the parsed JSON response.
    Raises BouncieAPIError on non-2xx responses.
    """
    url = f"{BASE_URL}{path}"
    response = requests.get(url, headers=_get_headers(), params=params, timeout=10)

    if not response.ok:
        raise BouncieAPIError(response.status_code, response.text)

    return response.json()


# ---------------------------------------------------------------------------
# Vehicles
# ---------------------------------------------------------------------------

def get_all_vehicles(imei: str = None, vin: str = None, limit: int = None, skip: int = None):
    """
    GET /v1/vehicles
    Supports optional server-side filtering:
      imei   – filter by device IMEI
      vin    – filter by VIN
      limit  – max results (paging)
      skip   – results to skip (paging)

    Each vehicle includes:
      model { make, name, year }, nickName, vin, imei, standardEngine
      stats {
        localTimeZone, odometer, lastUpdated, fuelLevel,
        isRunning, speed,
        location { lat, lon, heading },
        mil { on, codes[] }
      }
    """
    params = {}
    if imei:
        params["imei"] = imei
    if vin:
        params["vin"] = vin
    if limit is not None:
        params["limit"] = limit
    if skip is not None:
        params["skip"] = skip
    return _get("/vehicles", params=params or None)


def get_vehicle(imei: str):
    """
    Returns a single vehicle object filtered by IMEI using the
    server-side ?imei= parameter (no client-side loop needed).
    Raises BouncieAPIError(404) if the IMEI is not found.
    """
    vehicles = get_all_vehicles(imei=imei)
    if not vehicles:
        raise BouncieAPIError(404, f"Vehicle with IMEI {imei} not found.")
    return vehicles[0]


# ---------------------------------------------------------------------------
# Live location / stats
# ---------------------------------------------------------------------------

def get_vehicle_stats(imei: str):
    """
    Returns the full stats snapshot for a vehicle:
      localTimeZone, odometer, lastUpdated, fuelLevel,
      isRunning, speed,
      location { lat, lon, heading },
      mil { on, codes[] }
    """
    vehicle = get_vehicle(imei)
    return vehicle.get("stats", {})


def get_all_vehicles_live_location():
    """
    Returns live location + key stats for every vehicle in one call:
    [
      {
        imei, nickName, vin,
        location: { lat, lon, heading },
        speed, isRunning, odometer, fuelLevel, lastUpdated
      },
      ...
    ]
    """
    vehicles = get_all_vehicles()
    result = []
    for v in vehicles:
        stats = v.get("stats", {})
        result.append({
            "imei": v.get("imei"),
            "nickName": v.get("nickName"),
            "vin": v.get("vin"),
            "location": stats.get("location"),
            "speed": stats.get("speed"),
            "isRunning": stats.get("isRunning"),
            "odometer": stats.get("odometer"),
            "fuelLevel": stats.get("fuelLevel"),
            "lastUpdated": stats.get("lastUpdated"),
        })
    return result


# ---------------------------------------------------------------------------
# Trips  (also the source of historical GPS coordinates)
# ---------------------------------------------------------------------------

def get_trips(imei: str, starts_after: str = None, ends_before: str = None,
              gps_format: str = "polyline", transaction_id: str = None):
    """
    GET /v1/trips
    Returns trip history for a vehicle.

    Parameters:
      imei            – (required) device IMEI
      starts_after    – ISO 8601 e.g. "2026-01-01T00:00:00.000Z"
                        Defaults to last 7 days if omitted.
      ends_before     – ISO 8601  (window must be ≤ 7 days)
      gps_format      – "polyline" (default) | "geojson"
      transaction_id  – fetch a single specific trip by its ID

    Each trip includes:
      transactionId, imei, startTime, endTime,
      distance (miles), averageSpeed, maxSpeed,
      startOdometer, endOdometer, fuelConsumed,
      hardBrakingCount, hardAccelerationCount,
      totalIdleDuration, timeZone,
      gps  – encoded polyline or GeoJSON LineString of the full route
    """
    params = {"imei": imei, "gps-format": gps_format}
    if starts_after:
        params["starts-after"] = starts_after
    if ends_before:
        params["ends-before"] = ends_before
    if transaction_id:
        params["transaction-id"] = transaction_id
    return _get("/trips", params=params)


def get_vehicle_location_history(imei: str, starts_after: str = None, ends_before: str = None):
    """
    Returns the full list of GPS coordinates (lat/lon) a vehicle has visited,
    extracted from all trips in the requested time window.

    Uses gps-format=geojson so each trip's `gps` field is a GeoJSON
    LineString with a `coordinates` array of [lon, lat] pairs.

    Returns:
    [
      {
        "transactionId": "...",
        "startTime": "...",
        "endTime": "...",
        "distance": 12.5,
        "coordinates": [ [lon, lat], [lon, lat], ... ]
      },
      ...
    ]
    Note: coordinates are ordered [longitude, latitude] per GeoJSON spec.
    """
    trips = get_trips(
        imei=imei,
        starts_after=starts_after,
        ends_before=ends_before,
        gps_format="geojson",
    )

    result = []
    for trip in trips:
        gps = trip.get("gps") or {}
        # gps is a GeoJSON LineString: { "type": "LineString", "coordinates": [[lon,lat], ...] }
        coordinates = gps.get("coordinates", []) if isinstance(gps, dict) else []
        result.append({
            "transactionId": trip.get("transactionId"),
            "startTime": trip.get("startTime"),
            "endTime": trip.get("endTime"),
            "distance": trip.get("distance"),
            "coordinates": coordinates,
        })
    return result
