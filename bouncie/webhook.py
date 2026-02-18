"""
bouncie/webhook.py
------------------
Dedicated handlers for every Bouncie webhook event type.

Each handler receives the full decoded payload dict, persists one or more
VehicleEvent rows, and broadcasts a message to the Django Channels group
``vehicle_{imei}`` so connected WebSocket clients get real-time updates.

Entry point
-----------
    from bouncie.webhook import dispatch
    dispatch(payload)          # called from BouncieWebhookView.post()

Bouncie event types handled
----------------------------
    tripData            – real-time GPS point(s) during an active trip
    tripStart           – a new trip has begun
    tripEnd             – trip finished (summary data)
    tripMetrics         – periodic trip statistics
    deviceConnect       – device came online
    deviceDisconnect    – device went offline
    battery             – battery level / low-battery alert
    mil                 – MIL (check-engine / fault code) status change
    vinChange           – vehicle VIN was updated
    applicationGeoZone  – device entered/left an app-level geo-zone
    userGeoZone         – device entered/left a user-level geo-zone
"""

import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import VehicleEvent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _send(group_name: str, message: dict) -> None:
    """Push a message to a Django Channels group (fire-and-forget)."""
    channel_layer = get_channel_layer()
    if channel_layer:
        try:
            async_to_sync(channel_layer.group_send)(group_name, message)
        except Exception as exc:   # pragma: no cover
            logger.warning("channel_layer.group_send failed: %s", exc)


def _save_event(imei: str, event_type: str, payload: dict, **extra) -> VehicleEvent:
    """Persist a single VehicleEvent and return it."""
    return VehicleEvent.objects.create(
        imei=imei,
        event_type=event_type,
        transaction_id=payload.get("transactionId", ""),
        payload=payload,
        **extra,
    )


# ---------------------------------------------------------------------------
# Per-event handlers
# ---------------------------------------------------------------------------

def handle_trip_data(imei: str, payload: dict) -> None:
    """
    tripData
    --------
    Bouncie sends a batch of GPS points while a trip is active.
    Each point: { lat, lon, speed, heading, timestamp, ... }

    - Bulk-inserts one VehicleEvent per point.
    - Broadcasts each point individually to the vehicle group so clients
      draw a smooth, incrementally-updated track on the map.
    """
    gps_points = payload.get("tripData", [])
    transaction_id = payload.get("transactionId", "")
    group_name = f"vehicle_{imei}"

    if not gps_points:
        logger.debug("tripData webhook for %s contained no GPS points", imei)
        return

    rows = [
        VehicleEvent(
            imei=imei,
            event_type="tripData",
            transaction_id=transaction_id,
            payload=point,
            lat=point.get("lat"),
            lon=point.get("lon"),
            speed=point.get("speed"),
            heading=point.get("heading"),
        )
        for point in gps_points
    ]
    VehicleEvent.objects.bulk_create(rows)

    for point in gps_points:
        _send(
            group_name,
            {
                "type": "vehicle_location",
                "data": {
                    "event":         "tripData",
                    "imei":          imei,
                    "transactionId": transaction_id,
                    "lat":           point.get("lat"),
                    "lon":           point.get("lon"),
                    "speed":         point.get("speed"),
                    "heading":       point.get("heading"),
                    "timestamp":     point.get("timestamp"),
                },
            },
        )
    logger.debug("tripData: saved & broadcast %d points for %s", len(gps_points), imei)


def handle_trip_start(imei: str, payload: dict) -> None:
    """
    tripStart
    ---------
    The device reports a new trip has begun.
    Payload typically contains: transactionId, startTime, startOdometer, ...

    Clients receive the start event so they can open a new track on the map.
    """
    event = _save_event(imei, "tripStart", payload)
    _send(
        f"vehicle_{imei}",
        {
            "type": "vehicle_event",
            "data": {
                "event":         "tripStart",
                "imei":          imei,
                "transactionId": payload.get("transactionId", ""),
                "startTime":     payload.get("startTime"),
                "startOdometer": payload.get("startOdometer"),
            },
        },
    )
    logger.info("tripStart: imei=%s transactionId=%s", imei, payload.get("transactionId"))


def handle_trip_end(imei: str, payload: dict) -> None:
    """
    tripEnd
    -------
    Sent when a trip finishes.
    Payload typically contains: transactionId, startTime, endTime, distance,
    fuelConsumed, averageSpeed, ...

    Clients receive a summary so they can close the current track and
    display trip statistics.
    """
    event = _save_event(imei, "tripEnd", payload)
    _send(
        f"vehicle_{imei}",
        {
            "type": "vehicle_event",
            "data": {
                "event":          "tripEnd",
                "imei":           imei,
                "transactionId":  payload.get("transactionId", ""),
                "startTime":      payload.get("startTime"),
                "endTime":        payload.get("endTime"),
                "distance":       payload.get("distance"),
                "fuelConsumed":   payload.get("fuelConsumed"),
                "averageSpeed":   payload.get("averageSpeed"),
                "hardBrakeCount": payload.get("hardBrakeCount"),
                "hardAccelCount": payload.get("hardAccelCount"),
            },
        },
    )
    logger.info("tripEnd: imei=%s transactionId=%s", imei, payload.get("transactionId"))


def handle_trip_metrics(imei: str, payload: dict) -> None:
    """
    tripMetrics
    -----------
    Periodic statistics during an active trip (speed, fuel, odometer, …).
    Useful for live dashboards showing running averages.
    """
    event = _save_event(imei, "tripMetrics", payload)
    _send(
        f"vehicle_{imei}",
        {
            "type": "vehicle_event",
            "data": {
                "event":         "tripMetrics",
                "imei":          imei,
                "transactionId": payload.get("transactionId", ""),
                "payload":       payload,
            },
        },
    )
    logger.debug("tripMetrics: imei=%s", imei)


def handle_device_connect(imei: str, payload: dict) -> None:
    """
    deviceConnect
    -------------
    The OBD device powered on (engine started or USB power restored).
    Useful for tracking fleet ignition-on events.
    """
    event = _save_event(imei, "deviceConnect", payload)
    _send(
        f"vehicle_{imei}",
        {
            "type": "vehicle_event",
            "data": {
                "event":     "deviceConnect",
                "imei":      imei,
                "timestamp": payload.get("timestamp"),
            },
        },
    )
    logger.info("deviceConnect: imei=%s", imei)


def handle_device_disconnect(imei: str, payload: dict) -> None:
    """
    deviceDisconnect
    ----------------
    The OBD device lost power (engine off or USB disconnected).
    """
    event = _save_event(imei, "deviceDisconnect", payload)
    _send(
        f"vehicle_{imei}",
        {
            "type": "vehicle_event",
            "data": {
                "event":     "deviceDisconnect",
                "imei":      imei,
                "timestamp": payload.get("timestamp"),
            },
        },
    )
    logger.info("deviceDisconnect: imei=%s", imei)


def handle_battery(imei: str, payload: dict) -> None:
    """
    battery
    -------
    Battery voltage alert. Payload usually contains: voltage, alertType.
    alertType values: "low_battery", "critical_low_battery", etc.
    """
    event = _save_event(imei, "battery", payload)
    _send(
        f"vehicle_{imei}",
        {
            "type": "vehicle_event",
            "data": {
                "event":     "battery",
                "imei":      imei,
                "voltage":   payload.get("voltage"),
                "alertType": payload.get("alertType"),
                "timestamp": payload.get("timestamp"),
            },
        },
    )
    logger.warning("battery alert: imei=%s voltage=%s alertType=%s",
                   imei, payload.get("voltage"), payload.get("alertType"))


def handle_mil(imei: str, payload: dict) -> None:
    """
    mil (Malfunction Indicator Lamp / Check-Engine)
    -----------------------------------------------
    Sent when the check-engine lamp state changes.
    Payload: milStatus (on/off), dtcList (list of fault codes), ...
    """
    event = _save_event(imei, "mil", payload)
    _send(
        f"vehicle_{imei}",
        {
            "type": "vehicle_event",
            "data": {
                "event":     "mil",
                "imei":      imei,
                "milStatus": payload.get("milStatus"),
                "dtcList":   payload.get("dtcList", []),
                "timestamp": payload.get("timestamp"),
            },
        },
    )
    logger.warning("mil event: imei=%s status=%s codes=%s",
                   imei, payload.get("milStatus"), payload.get("dtcList"))


def handle_vin_change(imei: str, payload: dict) -> None:
    """
    vinChange
    ---------
    The VIN read from the OBD port has changed (vehicle swap or re-flash).
    Payload: oldVin, newVin.
    """
    event = _save_event(imei, "vinChange", payload)
    _send(
        f"vehicle_{imei}",
        {
            "type": "vehicle_event",
            "data": {
                "event":  "vinChange",
                "imei":   imei,
                "oldVin": payload.get("oldVin"),
                "newVin": payload.get("newVin"),
            },
        },
    )
    logger.info("vinChange: imei=%s %s -> %s",
                imei, payload.get("oldVin"), payload.get("newVin"))


def handle_application_geo_zone(imei: str, payload: dict) -> None:
    """
    applicationGeoZone
    ------------------
    Device entered or left an application-level (company-wide) geo-zone.
    Payload: geoZoneName, geoZoneType, crossingType (enter/exit),
             lat, lon, timestamp, ...
    """
    event = _save_event(imei, "applicationGeoZone", payload)
    _send(
        f"vehicle_{imei}",
        {
            "type": "vehicle_event",
            "data": {
                "event":        "applicationGeoZone",
                "imei":         imei,
                "geoZoneName":  payload.get("geoZoneName"),
                "geoZoneType":  payload.get("geoZoneType"),
                "crossingType": payload.get("crossingType"),
                "lat":          payload.get("lat"),
                "lon":          payload.get("lon"),
                "timestamp":    payload.get("timestamp"),
            },
        },
    )
    logger.info("applicationGeoZone: imei=%s zone=%s type=%s",
                imei, payload.get("geoZoneName"), payload.get("crossingType"))


def handle_user_geo_zone(imei: str, payload: dict) -> None:
    """
    userGeoZone
    -----------
    Device entered or left a user-level (personal) geo-zone.
    Same structure as applicationGeoZone but scoped to a single user.
    """
    event = _save_event(imei, "userGeoZone", payload)
    _send(
        f"vehicle_{imei}",
        {
            "type": "vehicle_event",
            "data": {
                "event":        "userGeoZone",
                "imei":         imei,
                "geoZoneName":  payload.get("geoZoneName"),
                "crossingType": payload.get("crossingType"),
                "lat":          payload.get("lat"),
                "lon":          payload.get("lon"),
                "timestamp":    payload.get("timestamp"),
            },
        },
    )
    logger.info("userGeoZone: imei=%s zone=%s type=%s",
                imei, payload.get("geoZoneName"), payload.get("crossingType"))


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_HANDLERS = {
    "tripData":           handle_trip_data,
    "tripStart":          handle_trip_start,
    "tripEnd":            handle_trip_end,
    "tripMetrics":        handle_trip_metrics,
    "deviceConnect":      handle_device_connect,
    "deviceDisconnect":   handle_device_disconnect,
    "battery":            handle_battery,
    "mil":                handle_mil,
    "vinChange":          handle_vin_change,
    "applicationGeoZone": handle_application_geo_zone,
    "userGeoZone":        handle_user_geo_zone,
}


def dispatch(payload: dict) -> str:
    """
    Main entry point called by BouncieWebhookView.

    Resolves the correct handler from the payload's ``eventType`` field,
    invokes it, and returns the event_type string.

    Unknown event types are logged as warnings and stored with a raw
    VehicleEvent so data is never silently dropped.
    """
    event_type = payload.get("eventType", "")
    imei = payload.get("imei", "")

    handler = _HANDLERS.get(event_type)
    if handler:
        handler(imei, payload)
    else:
        # Unknown / future event type – persist raw payload so nothing is lost
        logger.warning("Unknown Bouncie eventType %r for imei=%s – storing raw", event_type, imei)
        try:
            VehicleEvent.objects.create(
                imei=imei,
                event_type=event_type[:30],  # truncate to field max_length
                transaction_id=payload.get("transactionId", ""),
                payload=payload,
            )
        except Exception as exc:
            logger.error("Failed to store unknown event: %s", exc)

    return event_type
