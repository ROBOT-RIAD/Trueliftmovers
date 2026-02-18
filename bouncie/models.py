from django.db import models
from django.utils import timezone
from datetime import timedelta
import requests
from django.conf import settings


class BouncieToken(models.Model):
    """
    Global singleton that stores the company's Bouncie OAuth2 access token.
    Only one row ever exists (pk=1). The admin authorises once; the token is
    auto-refreshed transparently whenever it expires using the stored
    authorization code (Bouncie auth codes do not expire).
    """
    authorization_code = models.TextField(default='') 
    access_token = models.TextField()
    token_type = models.CharField(max_length=50, default='Bearer')
    expires_in = models.IntegerField(default=3600)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bouncie Token'
        verbose_name_plural = 'Bouncie Tokens'

    def __str__(self):
        return f"BouncieToken (updated {self.updated_at:%Y-%m-%d %H:%M})"

    @property
    def is_expired(self):
        return timezone.now() >= self.updated_at + timedelta(seconds=self.expires_in)

    def refresh(self):
        payload = {
            "client_id": settings.BOUNCIE_CLIENT_ID,
            "client_secret": settings.BOUNCIE_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": self.authorization_code,
            "redirect_uri": settings.BOUNCIE_REDIRECT_URI,
        }
        response = requests.post(
            "https://auth.bouncie.com/oauth/token",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        self.access_token = data["access_token"]
        self.token_type = data.get("token_type", "Bearer")
        self.expires_in = data.get("expires_in", 3600)
        self.save(update_fields=["access_token", "token_type", "expires_in", "updated_at"])
        return self

    @classmethod
    def get_valid_token(cls):
        token = cls.objects.first()
        if token is None:
            return None
        if token.is_expired:
            token.refresh()
        return token

    @classmethod
    def store(cls, authorization_code, access_token, token_type='Bearer', expires_in=3600):
        obj, _ = cls.objects.update_or_create(
            pk=1,
            defaults={
                'authorization_code': authorization_code,
                'access_token': access_token,
                'token_type': token_type,
                'expires_in': expires_in,
            },
        )
        return obj


# ---------------------------------------------------------------------------
# Webhook event storage
# ---------------------------------------------------------------------------

class VehicleEvent(models.Model):
    """
    Stores every incoming Bouncie webhook event.
    tripData events hold real-time GPS coordinates;
    other events (tripStart, tripEnd, deviceConnect, etc.) are also stored.
    """
    EVENT_TYPES = [
        ('tripData',          'Trip Data'),
        ('tripStart',         'Trip Start'),
        ('tripEnd',           'Trip End'),
        ('tripMetrics',       'Trip Metrics'),
        ('deviceConnect',     'Device Connect'),
        ('deviceDisconnect',  'Device Disconnect'),
        ('battery',           'Battery'),
        ('mil',               'MIL'),
        ('vinChange',         'VIN Change'),
        ('applicationGeoZone','Application Geo-Zone'),
        ('userGeoZone',       'User Geo-Zone'),
    ]

    imei            = models.CharField(max_length=20, db_index=True)
    event_type      = models.CharField(max_length=30, choices=EVENT_TYPES, db_index=True)
    transaction_id  = models.CharField(max_length=100, blank=True, null=True)
    payload         = models.JSONField()          # full raw webhook payload
    # Denormalised live-location fields (only set for tripData)
    lat             = models.FloatField(null=True, blank=True)
    lon             = models.FloatField(null=True, blank=True)
    speed           = models.FloatField(null=True, blank=True)
    heading         = models.FloatField(null=True, blank=True)
    received_at     = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Vehicle Event'
        verbose_name_plural = 'Vehicle Events'
        ordering = ['-received_at']

    def __str__(self):
        return f"{self.event_type} | {self.imei} | {self.received_at:%Y-%m-%d %H:%M:%S}"
