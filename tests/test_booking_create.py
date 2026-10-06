import allure
import pytest

from src.builders import booking_payload, without
from src.schemas import Booking, CreatedBooking

pytestmark = [pytest.mark.regression, allure.feature("Create booking")]


@pytest.mark.smoke
def test_create_booking_returns_id_and_echoes_payload(client, cleanup):
    payload = booking_payload()

    response = client.create_booking(payload)

    assert response.status_code == 200
    created = CreatedBooking.model_validate_json(response.text)
    cleanup(created.bookingid)
    assert created.booking.model_dump(mode="json") == payload


def test_created_booking_can_be_read_back(client, cleanup):
    payload = booking_payload()
    booking_id = client.create_booking(payload).json()["bookingid"]
    cleanup(booking_id)

    response = client.get_booking(booking_id)

    assert response.status_code == 200
    assert Booking.model_validate_json(response.text).model_dump(mode="json") == payload


def test_additionalneeds_is_optional(client, cleanup):
    payload = without(booking_payload(), "additionalneeds")

    response = client.create_booking(payload)

    assert response.status_code == 200
    cleanup(response.json()["bookingid"])
    assert "additionalneeds" not in response.json()["booking"]


@pytest.mark.parametrize("field", ["firstname", "lastname", "totalprice", "depositpaid", "bookingdates"])
def test_missing_required_field_is_rejected(client, field):
    response = client.create_booking(without(booking_payload(), field))

    # Quirk: validation errors surface as 500 Internal Server Error, not 400.
    assert response.status_code == 500


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"firstname": 123}, id="firstname as number"),
        pytest.param({"bookingdates": "2030-06-10"}, id="bookingdates as string"),
    ],
)
def test_wrong_type_is_rejected(client, overrides):
    response = client.create_booking(booking_payload(**overrides))

    # Quirk: 500 instead of 400.
    assert response.status_code == 500


@pytest.mark.xfail(reason="API bug: API accepts a non-numeric price and stores it as null")
def test_non_numeric_price_is_rejected(client, cleanup):
    response = client.create_booking(booking_payload(totalprice="abc"))
    if response.status_code == 200:
        cleanup(response.json()["bookingid"])

    assert response.status_code in (400, 500)


@pytest.mark.xfail(reason='API bug: API accepts an invalid date and stores "0NaN-aN-aN"')
def test_invalid_date_is_rejected(client, cleanup):
    payload = booking_payload(bookingdates={"checkin": "not-a-date", "checkout": "2030-06-15"})
    response = client.create_booking(payload)
    if response.status_code == 200:
        cleanup(response.json()["bookingid"])

    assert response.status_code in (400, 500)
