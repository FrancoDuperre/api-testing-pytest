import allure
import pytest

from src.schemas import Booking, BookingId

pytestmark = [pytest.mark.regression, allure.feature("Read booking")]


@pytest.mark.smoke
def test_get_booking_by_id(client, booking):
    booking_id, payload = booking

    response = client.get_booking(booking_id)

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    assert Booking.model_validate_json(response.text).model_dump(mode="json") == payload


def test_get_booking_as_xml(client, booking):
    booking_id, payload = booking

    response = client.get_booking(booking_id, accept="application/xml")

    assert response.status_code == 200
    # Quirk: the body is XML but the Content-Type header says text/html.
    assert response.text.lstrip().startswith("<?xml")
    assert f"<firstname>{payload['firstname']}</firstname>" in response.text


@pytest.mark.parametrize("booking_id", [999999999, "not-a-number"])
def test_get_nonexistent_booking_returns_404(client, booking_id):
    response = client.get_booking(booking_id)

    assert response.status_code == 404


def test_list_contains_created_booking(client, booking):
    booking_id, _ = booking

    response = client.get_booking_ids()

    assert response.status_code == 200
    ids = [BookingId.model_validate(item).bookingid for item in response.json()]
    assert booking_id in ids


def ids_for(client, **filters) -> list[int]:
    response = client.get_booking_ids(**filters)
    assert response.status_code == 200
    return [item["bookingid"] for item in response.json()]


def test_filter_by_name(client, booking):
    booking_id, payload = booking

    ids = ids_for(client, firstname=payload["firstname"], lastname=payload["lastname"])

    assert ids == [booking_id]


def test_name_filter_is_case_sensitive(client, booking):
    _, payload = booking

    assert ids_for(client, firstname=payload["firstname"].upper()) == []


def test_filter_with_no_match_returns_empty_list(client):
    assert ids_for(client, firstname="NoSuchGuest_8c1f0e") == []


# The booking fixture checks in on 2030-06-10 and checks out on 2030-06-15.
@pytest.mark.parametrize(
    "filters, included",
    [
        pytest.param({"checkin": "2030-06-09"}, True, id="checkin day before"),
        # Docs say "greater than or equal", but the same day is excluded.
        pytest.param({"checkin": "2030-06-10"}, False, id="checkin same day"),
        # Docs say checkout is "greater than or equal"; the API actually returns
        # bookings that check out on or before the given date.
        pytest.param({"checkout": "2030-06-15"}, True, id="checkout same day"),
        pytest.param({"checkout": "2030-06-16"}, True, id="checkout day after"),
        pytest.param({"checkout": "2030-06-14"}, False, id="checkout day before"),
    ],
)
def test_filter_by_dates(client, booking, filters, included):
    booking_id, payload = booking

    ids = ids_for(client, firstname=payload["firstname"], **filters)

    assert (booking_id in ids) is included
