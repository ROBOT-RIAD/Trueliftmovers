import secrets
import requests
import logging

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminRole
from .models import BouncieToken
from . import bouncie as bouncie_service
from .bouncie import BouncieNotAuthorized, BouncieAPIError
from . import webhook as bouncie_webhook

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Bouncie OAuth2 constants
# ---------------------------------------------------------------------------
BOUNCIE_AUTH_URL = "https://auth.bouncie.com/dialog/authorize"
BOUNCIE_TOKEN_URL = "https://auth.bouncie.com/oauth/token"

CLIENT_ID = settings.BOUNCIE_CLIENT_ID
CLIENT_SECRET = settings.BOUNCIE_CLIENT_SECRET
REDIRECT_URI = settings.BOUNCIE_REDIRECT_URI

# Cache key prefix + TTL (10 minutes is more than enough for a browser round-trip)
STATE_CACHE_PREFIX = "bouncie_oauth_state_"
STATE_TTL = 600  # seconds


class BouncieAuthorizeView(APIView):
    """
    GET /bouncie/authorize/

    Admin-only. Generates a random CSRF state, caches it, then returns the
    Bouncie authorization URL for the admin to open in their browser.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        state = secrets.token_urlsafe(32)
        # Mark state as valid — value doesn't matter, just needs to exist
        cache.set(f"{STATE_CACHE_PREFIX}{state}", True, STATE_TTL)

        params = {
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "state": state,
        }
        auth_url = requests.Request("GET", BOUNCIE_AUTH_URL, params=params).prepare().url
        return Response({"authorization_url": auth_url}, status=status.HTTP_200_OK)


class BouncieCallbackView(APIView):
    """
    GET /callback/

    Bouncie redirects the user's browser here after they grant permission.
    Query params:  ?code=<auth_code>&state=<state>

    This view:
    1. Validates the state to find the correct user.
    2. Exchanges the authorization code for an access token.
    3. Persists the token in the BouncieToken table.
    """
    permission_classes = [AllowAny]  # Bouncie browser redirect – no JWT header

    def get(self, request):
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        error = request.query_params.get("error")

        if error:
            return Response(
                {"error": f"Bouncie authorization was denied: {error}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not code or not state:
            return Response(
                {"error": "Missing 'code' or 'state' query parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 1. Validate state ────────────────────────────────────────────────
        cache_key = f"{STATE_CACHE_PREFIX}{state}"
        valid = cache.get(cache_key)
        if not valid:
            return Response(
                {"error": "Invalid or expired state. Please restart the authorization flow."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cache.delete(cache_key)  # one-time use

        # ── 2. Exchange authorization code for access token ─────────────────
        payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        }
        try:
            token_response = requests.post(
                BOUNCIE_TOKEN_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            token_response.raise_for_status()
        except requests.RequestException as exc:
            return Response(
                {"error": f"Failed to obtain access token from Bouncie: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        token_type = token_data.get("token_type", "Bearer")
        expires_in = token_data.get("expires_in", 3600)

        if not access_token:
            return Response(
                {"error": "Bouncie did not return an access token.", "details": token_data},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # ── 3. Persist / update the global company token ────────────────────
        BouncieToken.store(code, access_token, token_type, expires_in)

        return Response(
            {"message": "Bouncie authorization successful. Access token stored."},
            status=status.HTTP_200_OK,
        )


# ===========================================================================
# Shared error handler helper
# ===========================================================================

def _bouncie_error_response(exc):
    if isinstance(exc, BouncieNotAuthorized):
        return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    if isinstance(exc, BouncieAPIError):
        return Response({"error": exc.detail}, status=exc.status_code)
    return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===========================================================================
# Vehicle views
# ===========================================================================

class VehicleListView(APIView):
    """
    GET /bouncie/vehicles/
    Returns all vehicles connected to the Bouncie account.
    Accessible by any authenticated user.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            data = bouncie_service.get_all_vehicles()
            return Response(data, status=status.HTTP_200_OK)
        except (BouncieNotAuthorized, BouncieAPIError) as exc:
            return _bouncie_error_response(exc)


class VehicleDetailView(APIView):
    """
    GET /bouncie/vehicles/{imei}/
    Returns details for a single vehicle.
    """
    permission_classes = [AllowAny]

    def get(self, request, imei):
        try:
            data = bouncie_service.get_vehicle(imei)
            return Response(data, status=status.HTTP_200_OK)
        except (BouncieNotAuthorized, BouncieAPIError) as exc:
            return _bouncie_error_response(exc)


# ===========================================================================
# Live location views
# ===========================================================================

class VehicleLiveLocationView(APIView):
    """
    GET /bouncie/vehicles/{imei}/location/
    Returns live location + stats for a single vehicle:
      lat, lon, heading, speed, isMoving, battery, lastUpdated
    """
    permission_classes = [AllowAny]

    def get(self, request, imei):
        try:
            data = bouncie_service.get_vehicle_stats(imei)
            return Response(data, status=status.HTTP_200_OK)
        except (BouncieNotAuthorized, BouncieAPIError) as exc:
            return _bouncie_error_response(exc)


class AllVehiclesLiveLocationView(APIView):
    """
    GET /bouncie/vehicles/location/
    Returns live location for ALL vehicles in one call.
    [
      { imei, customVehicleName, vin, location: {lat, lon, heading, speed, isMoving}, lastUpdated },
      ...
    ]
    """
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            data = bouncie_service.get_all_vehicles_live_location()
            return Response(data, status=status.HTTP_200_OK)
        except (BouncieNotAuthorized, BouncieAPIError) as exc:
            return _bouncie_error_response(exc)


# ===========================================================================
# Trip views
# ===========================================================================

class VehicleTripsView(APIView):
    """
    GET /bouncie/vehicles/{imei}/trips/
    Returns trip history for a vehicle.

    Optional query params:
      starts_after    : ISO 8601  e.g. 2026-01-01T00:00:00.000Z
      ends_before     : ISO 8601  (window must be ≤ 7 days)
      gps_format      : polyline (default) | geojson
      transaction_id  : fetch a single specific trip
    """
    permission_classes = [AllowAny]

    def get(self, request, imei):
        try:
            data = bouncie_service.get_trips(
                imei=imei,
                starts_after=request.query_params.get("starts_after"),
                ends_before=request.query_params.get("ends_before"),
                gps_format=request.query_params.get("gps_format", "polyline"),
                transaction_id=request.query_params.get("transaction_id"),
            )
            return Response(data, status=status.HTTP_200_OK)
        except (BouncieNotAuthorized, BouncieAPIError) as exc:
            return _bouncie_error_response(exc)


class VehicleLocationHistoryView(APIView):
    """
    GET /bouncie/vehicles/{imei}/location/history/
    Returns all GPS coordinates the vehicle has visited, grouped by trip.

    Bouncie stores historical positions inside trip records (gps-format=geojson).
    The window between starts_after and ends_before must be ≤ 7 days.
    Defaults to the last 7 days if no dates are provided.

    Optional query params:
      starts_after  : ISO 8601  e.g. 2026-01-01T00:00:00.000Z
      ends_before   : ISO 8601

    Response:
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
    Note: coordinates are [longitude, latitude] per GeoJSON spec.
    """
    permission_classes = [AllowAny]

    def get(self, request, imei):
        try:
            data = bouncie_service.get_vehicle_location_history(
                imei=imei,
                starts_after=request.query_params.get("starts_after"),
                ends_before=request.query_params.get("ends_before"),
            )
            return Response(data, status=status.HTTP_200_OK)
        except (BouncieNotAuthorized, BouncieAPIError) as exc:
            return _bouncie_error_response(exc)


class BouncieWebhookView(APIView):
    """
    POST /bouncie/webhook/

    Validates the Authorization header against settings.BOUNCIE_WEBHOOK_KEY,
    then delegates all event-specific logic to bouncie/webhook.py.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        # --- auth ---
        webhook_key = settings.BOUNCIE_WEBHOOK_KEY
        auth_header = (
            request.headers.get("Authorization")
            or request.headers.get("X-Bouncie-Authorization", "")
        )
        if webhook_key and auth_header != webhook_key:
            return Response(
                {"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED
            )

        payload = request.data  # DRF already parsed JSON

        if not payload.get("imei"):
            return Response(
                {"detail": "Missing imei"}, status=status.HTTP_400_BAD_REQUEST
            )

        event_type = bouncie_webhook.dispatch(payload)

        return Response({"status": "ok", "eventType": event_type}, status=status.HTTP_200_OK)
