import secrets
import requests

from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminRole
from .models import BouncieToken

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
