import os
import platform
import time
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

from src.builders import booking_payload
from src.client import BookingClient, TokenAuth

load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        pytest.exit(f"Missing environment variable {name}. Copy .env.example to .env.", returncode=2)
    return value


def pytest_sessionfinish(session):
    """Fill the Environment widget of the Allure report when --alluredir is used."""
    alluredir = session.config.getoption("allure_report_dir", default=None)
    if alluredir:
        Path(alluredir, "environment.properties").write_text(
            f"Base.URL={os.getenv('BASE_URL', 'http://localhost:3001')}\n"
            f"Python={platform.python_version()}\n"
        )


@pytest.fixture(scope="session")
def credentials() -> tuple[str, str]:
    return require_env("BOOKER_USERNAME"), require_env("BOOKER_PASSWORD")


def wait_until_ready(client: BookingClient, timeout: float = 30) -> bool:
    """A container can report healthy before its port is reachable from the host,
    so poll /ping instead of failing the whole session on the first refused connection."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            if client.ping().status_code == 201:
                return True
        except requests.ConnectionError:
            pass
        if time.monotonic() >= deadline:
            return False
        time.sleep(1)


@pytest.fixture(scope="session")
def client() -> BookingClient:
    client = BookingClient(os.getenv("BASE_URL", "http://localhost:3001"))
    if not wait_until_ready(client):
        pytest.exit(f"Restful-Booker is not reachable at {client.base_url}", returncode=2)
    return client


@pytest.fixture(scope="session")
def token_auth(client, credentials) -> TokenAuth:
    response = client.create_token(*credentials)
    assert response.status_code == 200, response.text
    return TokenAuth(response.json()["token"])


@pytest.fixture(scope="session")
def basic_auth(credentials) -> HTTPBasicAuth:
    return HTTPBasicAuth(*credentials)


@pytest.fixture
def cleanup(client, token_auth):
    """Collects booking ids created by a test and deletes them afterwards.
    Deleting an already-deleted booking returns 405, which is fine here."""
    ids: list[int] = []
    yield ids.append
    for booking_id in ids:
        client.delete_booking(booking_id, auth=token_auth)


@pytest.fixture
def create_booking(client, cleanup):
    """Factory: creates a booking (optionally customised) that is deleted after the test."""

    def _create(**overrides) -> tuple[int, dict]:
        payload = booking_payload(**overrides)
        response = client.create_booking(payload)
        assert response.status_code == 200, response.text
        booking_id = response.json()["bookingid"]
        cleanup(booking_id)
        return booking_id, payload

    return _create


@pytest.fixture
def booking(create_booking) -> tuple[int, dict]:
    """A default booking that exists for the duration of one test."""
    return create_booking()
