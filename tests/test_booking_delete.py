import allure
import pytest

pytestmark = [pytest.mark.regression, allure.feature("Delete booking")]


@pytest.mark.smoke
def test_delete_with_token_removes_booking(client, booking, token_auth):
    booking_id, _ = booking

    response = client.delete_booking(booking_id, auth=token_auth)

    # Quirk: a successful delete returns 201 Created (documented, but unusual).
    assert response.status_code == 201
    assert client.get_booking(booking_id).status_code == 404


def test_delete_with_basic_auth(client, booking, basic_auth):
    booking_id, _ = booking

    response = client.delete_booking(booking_id, auth=basic_auth)

    assert response.status_code == 201
    assert client.get_booking(booking_id).status_code == 404


def test_delete_twice(client, booking, token_auth):
    booking_id, _ = booking
    client.delete_booking(booking_id, auth=token_auth)

    response = client.delete_booking(booking_id, auth=token_auth)

    # Quirk: 405 Method Not Allowed instead of 404 Not Found.
    assert response.status_code == 405


def test_delete_nonexistent_booking(client, token_auth):
    response = client.delete_booking(999999999, auth=token_auth)

    assert response.status_code == 405
