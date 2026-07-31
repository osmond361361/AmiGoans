import ipaddress

import requests
from flask import current_app

from app.extensions import db
from app.models import IpLocation

UNKNOWN_LOCATION = {"city": None, "region": None, "country": None}


def _is_private_ip(ip_address):
    try:
        return ipaddress.ip_address(ip_address).is_private
    except ValueError:
        return True


def resolve_ip_location(ip_address):
    """Return {"city", "region", "country"} for an IP, using a cached lookup.

    Private/loopback addresses and lookup failures resolve to unknown
    values without hitting the external service or being cached, so a
    later real address can still be looked up.
    """
    cached = IpLocation.query.filter_by(ip_address=ip_address).first()
    if cached is not None:
        return {"city": cached.city, "region": cached.region, "country": cached.country}

    if _is_private_ip(ip_address):
        db.session.add(IpLocation(ip_address=ip_address, is_private=True, **UNKNOWN_LOCATION))
        db.session.commit()
        return UNKNOWN_LOCATION

    try:
        response = requests.get(
            f"http://ip-api.com/json/{ip_address}",
            params={"fields": "status,city,regionName,country"},
            timeout=3,
        )
        data = response.json()
    except (requests.RequestException, ValueError):
        current_app.logger.warning("IP geolocation lookup failed for %s", ip_address)
        return UNKNOWN_LOCATION

    if data.get("status") != "success":
        return UNKNOWN_LOCATION

    location = {
        "city": data.get("city"),
        "region": data.get("regionName"),
        "country": data.get("country"),
    }
    db.session.add(IpLocation(ip_address=ip_address, is_private=False, **location))
    db.session.commit()
    return location
