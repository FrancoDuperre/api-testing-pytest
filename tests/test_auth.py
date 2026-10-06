import allure
import pytest
from requests.auth import HTTPBasicAuth

from src.client import TokenAuth
from src.schemas import AuthFailure, Token

pytestmark = [pytest.mark.regression, allure.feature("Authentication")]


@pytest.mark.smoke
def test_valid_credentials_return_a_token(client, credentials):
    response = client.create_token(*credentials)

    assert response.status_code == 200
    assert Token.model_validate_json(response.text).token


def invalid_credentials(case: str, username: str, password: str) -> tuple[str, str]:
    return {
        "wrong password": (username, "wrong-password"),
        "unknown user": ("not-a-user", password),
        "empty credentials": ("", ""),
    }[case]


@pytest.mark.parametrize("case", ["wrong password", "unknown user", "empty credentials"])
def test_invalid_credentials_are_rejected(client, credentials, case):
    response = client.create_token(*invalid_credentials(case, *credentials))

    # Quirk: failed auth returns 200 with a "reason" body instead of 401.
    assert response.status_code == 200
    assert AuthFailure.model_validate_json(response.text).reason == "Bad credentials"


def write(client, method: str, booking_id: int, auth):
    if method == "PUT":
        return client.update_booking(booking_id, {"firstname": "X"}, auth=auth)
    if method == "PATCH":
        return client.partial_update_booking(booking_id, {"firstname": "X"}, auth=auth)
    return client.delete_booking(booking_id, auth=auth)


WRITE_METHODS = ["PUT", "PATCH", "DELETE"]


@pytest.mark.parametrize("method", WRITE_METHODS)
def test_write_without_auth_is_forbidden(client, booking, method):
    booking_id, payload = booking

    response = write(client, method, booking_id, auth=None)

    assert response.status_code == 403
    assert client.get_booking(booking_id).json() == payload


@pytest.mark.parametrize("auth_case", ["invalid token", "wrong basic auth password"])
@pytest.mark.parametrize("method", WRITE_METHODS)
def test_write_with_invalid_auth_is_forbidden(client, credentials, booking, method, auth_case):
    booking_id, payload = booking
    auth = (
        TokenAuth("not-a-real-token")
        if auth_case == "invalid token"
        else HTTPBasicAuth(credentials[0], "wrong-password")
    )

    response = write(client, method, booking_id, auth)

    assert response.status_code == 403
    assert client.get_booking(booking_id).json() == payload
