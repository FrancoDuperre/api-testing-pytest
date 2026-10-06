"""Thin wrapper over requests for the Restful-Booker API.

Methods return the raw `requests.Response` so tests can assert on status codes,
headers and bodies, including the API's unusual error responses.
"""

import allure
import requests
from requests.auth import AuthBase


class TokenAuth(AuthBase):
    """Sends the token from POST /auth as the `token` cookie, as the API expects."""

    def __init__(self, token: str):
        self.token = token

    def __call__(self, request):
        request.headers["Cookie"] = f"token={self.token}"
        return request


class BookingClient:
    def __init__(self, base_url: str, timeout: float = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        with allure.step(f"{method} {path}"):
            response = self.session.request(
                method, f"{self.base_url}{path}", timeout=self.timeout, **kwargs
            )
            allure.attach(
                response.text,
                name=f"{response.status_code} response",
                attachment_type=allure.attachment_type.TEXT,
            )
            return response

    def ping(self) -> requests.Response:
        return self._request("GET", "/ping")

    def create_token(self, username: str, password: str) -> requests.Response:
        return self._request("POST", "/auth", json={"username": username, "password": password})

    def get_booking_ids(self, **filters) -> requests.Response:
        return self._request("GET", "/booking", params=filters)

    def get_booking(self, booking_id, accept: str = "application/json") -> requests.Response:
        return self._request("GET", f"/booking/{booking_id}", headers={"Accept": accept})

    def create_booking(self, payload: dict) -> requests.Response:
        return self._request("POST", "/booking", json=payload)

    def update_booking(self, booking_id, payload: dict, auth: AuthBase | None = None) -> requests.Response:
        return self._request("PUT", f"/booking/{booking_id}", json=payload, auth=auth)

    def partial_update_booking(self, booking_id, payload: dict, auth: AuthBase | None = None) -> requests.Response:
        return self._request("PATCH", f"/booking/{booking_id}", json=payload, auth=auth)

    def delete_booking(self, booking_id, auth: AuthBase | None = None) -> requests.Response:
        return self._request("DELETE", f"/booking/{booking_id}", auth=auth)
