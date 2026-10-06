"""Payload builders. Every booking gets a unique first name so tests that filter
the booking list stay deterministic, even on the shared public instance."""

import copy
from uuid import uuid4


def unique_name(prefix: str = "Test") -> str:
    return f"{prefix}{uuid4().hex[:10]}"


def booking_payload(**overrides) -> dict:
    payload = {
        "firstname": unique_name(),
        "lastname": "Booker",
        "totalprice": 150,
        "depositpaid": True,
        "bookingdates": {"checkin": "2030-06-10", "checkout": "2030-06-15"},
        "additionalneeds": "Breakfast",
    }
    payload.update(overrides)
    return payload


def without(payload: dict, field: str) -> dict:
    """Copy of the payload with one top-level field removed."""
    result = copy.deepcopy(payload)
    result.pop(field)
    return result
