import allure
import pytest

from src.builders import booking_payload
from src.schemas import Booking

pytestmark = [pytest.mark.regression, allure.feature("Update booking")]


@pytest.mark.smoke
def test_full_update_with_token(client, booking, token_auth):
    booking_id, _ = booking
    new_payload = booking_payload(lastname="Updated", totalprice=999, depositpaid=False)

    response = client.update_booking(booking_id, new_payload, auth=token_auth)

    assert response.status_code == 200
    assert Booking.model_validate_json(response.text).model_dump(mode="json") == new_payload
    assert client.get_booking(booking_id).json() == new_payload


def test_full_update_with_basic_auth(client, booking, basic_auth):
    booking_id, _ = booking
    new_payload = booking_payload(totalprice=321)

    response = client.update_booking(booking_id, new_payload, auth=basic_auth)

    assert response.status_code == 200
    assert client.get_booking(booking_id).json() == new_payload


def test_full_update_with_partial_body_is_rejected(client, booking, token_auth):
    booking_id, payload = booking

    response = client.update_booking(booking_id, {"firstname": "OnlyName"}, auth=token_auth)

    assert response.status_code == 400
    assert client.get_booking(booking_id).json() == payload


def test_partial_update_changes_only_given_fields(client, booking, token_auth):
    booking_id, payload = booking
    changes = {"firstname": "Patched", "totalprice": 42}

    response = client.partial_update_booking(booking_id, changes, auth=token_auth)

    assert response.status_code == 200
    assert response.json() == {**payload, **changes}
    assert client.get_booking(booking_id).json() == {**payload, **changes}


@pytest.mark.parametrize("method", ["PUT", "PATCH"])
def test_update_nonexistent_booking(client, token_auth, method):
    if method == "PUT":
        response = client.update_booking(999999999, booking_payload(), auth=token_auth)
    else:
        response = client.partial_update_booking(999999999, {"firstname": "X"}, auth=token_auth)

    # Quirk: 405 Method Not Allowed instead of 404 Not Found.
    assert response.status_code == 405


@pytest.mark.xfail(reason="API bug: patching only bookingdates.checkout corrupts checkin to 0NaN-aN-aN")
def test_partial_update_of_nested_checkout_keeps_checkin(client, booking, token_auth):
    booking_id, payload = booking

    response = client.partial_update_booking(
        booking_id, {"bookingdates": {"checkout": "2030-06-20"}}, auth=token_auth
    )

    assert response.status_code == 200
    assert response.json()["bookingdates"] == {
        "checkin": payload["bookingdates"]["checkin"],
        "checkout": "2030-06-20",
    }
