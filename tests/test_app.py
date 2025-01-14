import json
from http import HTTPStatus

import pytest

from app import app


class StatusApiClient:
    """Client for interacting with the Status API"""

    def __init__(self, client) -> None:
        self.client = client

    def get_status(self) -> tuple[int, str | None]:
        """Get current version status"""
        response = self.client.get("/status")
        data = json.loads(response.data)
        return response.status_code, data["version"]

    def set_status(self) -> int:
        """Set initial version status"""
        response = self.client.post("/setStatus")
        return response.status_code

    def update_status(self) -> int:
        """Update to next minor version"""
        response = self.client.patch("/updateStatus")
        return response.status_code

    def rewrite_status(self) -> int:
        """Rewrite to next major version"""
        response = self.client.put("/rewriteStatus")
        return response.status_code

    def remove_status(self) -> int:
        """Remove version status"""
        response = self.client.delete("/removeStatus")
        return response.status_code

    def rollback_status(self, version: str | None = None) -> int:
        """Rollback to previous or specific version"""
        data = {"version": version} if version else {}
        response = self.client.post("/rollbackStatusVersion", json=data)
        return response.status_code


@pytest.fixture
def client():
    """Create a test client"""
    app.testing = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def api_client(client) -> StatusApiClient:
    """Create API client instance"""
    return StatusApiClient(client)


@pytest.fixture
def clean_state(api_client):
    """Clean version state before each test"""
    status_code = api_client.remove_status()
    assert status_code == HTTPStatus.OK

    status_code, version = api_client.get_status()
    assert version is None


@pytest.fixture
def no_version_state(clean_state, api_client) -> StatusApiClient:
    """Setup: No version set"""
    return api_client


@pytest.fixture
def version_1_state(clean_state, api_client) -> StatusApiClient:
    """Setup: Version 1 set"""
    api_client.set_status()
    status_code, version = api_client.get_status()
    assert version == "1"
    return api_client


@pytest.fixture
def version_1_1_state(version_1_state, api_client) -> StatusApiClient:
    """Setup: Version 1.1 set"""
    api_client.update_status()
    status_code, version = api_client.get_status()
    assert version == "1.1"
    return api_client


@pytest.fixture
def version_2_state(version_1_1_state, api_client) -> StatusApiClient:
    """Setup: Version 2 set"""
    api_client.rewrite_status()
    status_code, version = api_client.get_status()
    assert version == "2"
    return api_client


class TestStatusEndpoint:
    """Tests for GET /status endpoint"""

    def test_get_status_no_version(self, no_version_state):
        status_code, version = no_version_state.get_status()
        assert status_code == HTTPStatus.NOT_FOUND
        assert version is None

    def test_get_status_version_1(self, version_1_state):
        status_code, version = version_1_state.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "1"

    def test_get_status_version_1_1(self, version_1_1_state):
        status_code, version = version_1_1_state.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "1.1"

    def test_get_status_version_2(self, version_2_state):
        status_code, version = version_2_state.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "2"


class TestSetStatusEndpoint:
    """Tests for POST /setStatus endpoint"""

    def test_set_status_when_no_version(self, no_version_state):
        status_code = no_version_state.set_status()
        assert status_code == HTTPStatus.CREATED

        status_code, version = no_version_state.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "1"

    def test_set_status_when_version_exists(self, version_1_state):
        status_code = version_1_state.set_status()
        assert status_code == HTTPStatus.BAD_REQUEST

        status_code, version = version_1_state.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "1"


class TestUpdateStatusEndpoint:
    """Tests for PATCH /updateStatus endpoint"""

    def test_update_status_no_version(self, no_version_state):
        status_code = no_version_state.update_status()
        assert status_code == HTTPStatus.BAD_REQUEST

        status_code, version = no_version_state.get_status()
        assert status_code == HTTPStatus.NOT_FOUND
        assert version is None

    def test_update_status_from_version_1(self, version_1_state):
        status_code = version_1_state.update_status()
        assert status_code == HTTPStatus.OK

        status_code, version = version_1_state.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "1.1"

    def test_update_status_from_version_1_1(self, version_1_1_state):
        status_code = version_1_1_state.update_status()
        assert status_code == HTTPStatus.OK

        status_code, version = version_1_1_state.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "1.2"

    def test_update_status_from_version_2(self, version_2_state):
        status_code = version_2_state.update_status()
        assert status_code == HTTPStatus.OK

        status_code, version = version_2_state.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "2.1"


class TestRewriteStatusEndpoint:
    """Tests for PUT /rewriteStatus endpoint"""

    def test_rewrite_status_no_version(self, no_version_state):
        status_code = no_version_state.rewrite_status()
        assert status_code == HTTPStatus.BAD_REQUEST

        status_code, version = no_version_state.get_status()
        assert status_code == HTTPStatus.NOT_FOUND
        assert version is None

    def test_rewrite_status_from_version_1(self, version_1_state):
        status_code = version_1_state.rewrite_status()
        assert status_code == HTTPStatus.OK

        status_code, versione = version_1_state.get_status()
        assert status_code == HTTPStatus.OK
        assert versione == "2"

    def test_rewrite_status_from_version_1_1(self, version_1_1_state):
        status_code = version_1_1_state.rewrite_status()
        assert status_code == HTTPStatus.OK

        status_code, version = version_1_1_state.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "2"


class TestRemoveStatusEndpoint:
    """Tests for DELETE /removeStatus endpoint"""

    def test_remove_status_no_version(self, no_version_state):
        status_code = no_version_state.remove_status()
        assert status_code == HTTPStatus.OK

        status_code, version = no_version_state.get_status()
        assert status_code == HTTPStatus.NOT_FOUND
        assert version is None

    def test_remove_status_from_version_1(self, version_1_state):
        status_code = version_1_state.remove_status()
        assert status_code == HTTPStatus.OK

        status_code, version = version_1_state.get_status()
        assert status_code == HTTPStatus.NOT_FOUND
        assert version is None

    def test_remove_status_from_version_2(self, version_2_state):
        status_code = version_2_state.remove_status()
        assert status_code == HTTPStatus.OK

        status_code, version = version_2_state.get_status()
        assert status_code == HTTPStatus.NOT_FOUND
        assert version is None


class TestRollbackStatusEndpoint:
    """Tests for POST /rollbackStatusVersion endpoint"""

    def test_rollback_status_no_version(self, no_version_state):
        status_code = no_version_state.rollback_status()
        assert status_code == HTTPStatus.BAD_REQUEST

        status_code, version = no_version_state.get_status()
        assert status_code == HTTPStatus.NOT_FOUND
        assert version is None

    def test_rollback_status_from_version_1(self, version_1_state):
        status_code = version_1_state.rollback_status()
        assert status_code == HTTPStatus.BAD_REQUEST

        status_code, version = version_1_state.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "1"

    def test_rollback_status_from_version_2(self, version_2_state):
        status_code = version_2_state.rollback_status()
        assert status_code == HTTPStatus.OK

        status_code, version = version_2_state.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "1"

    def test_rollback_to_specific_version(self, version_2_state):
        status_code = version_2_state.rollback_status("1.1")
        assert status_code == HTTPStatus.OK

        status_code, version = version_2_state.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "1.1"

    def test_rollback_to_invalid_version(self, version_2_state):
        status_code = version_2_state.rollback_status("5")
        assert status_code == HTTPStatus.BAD_REQUEST

        status_code, version = version_2_state.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "2"


class TestStateTransitions:
    """Tests for complex state transitions"""

    def test_full_version_lifecycle(self, no_version_state):
        # Start with no version
        status_code, version = no_version_state.get_status()
        assert status_code == HTTPStatus.NOT_FOUND
        assert version is None

        # Set initial version
        status_code = no_version_state.set_status()
        assert status_code == HTTPStatus.CREATED

        status_code, version = no_version_state.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "1"

        # Update to minor version
        status_code = no_version_state.update_status()
        assert status_code == HTTPStatus.OK

        status_code, version = no_version_state.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "1.1"

        # Update to another minor version
        status_code = no_version_state.update_status()
        assert status_code == HTTPStatus.OK

        status_code, version = no_version_state.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "1.2"

        # Rewrite to major version
        status_code = no_version_state.rewrite_status()
        assert status_code == HTTPStatus.OK

        status_code, version = no_version_state.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "2"

        # Rollback to previous major
        status_code = no_version_state.rollback_status()
        assert status_code == HTTPStatus.OK

        status_code, version = no_version_state.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "1"

        # Remove status
        status_code = no_version_state.remove_status()
        assert status_code == HTTPStatus.OK

        status_code, version = no_version_state.get_status()
        assert status_code == HTTPStatus.NOT_FOUND
        assert version is None

    def test_multiple_minor_updates(self, version_1_state):
        expected_versions = ["1.1", "1.2", "1.3"]
        for expected_version in expected_versions:
            status_code = version_1_state.update_status()
            assert status_code == HTTPStatus.OK

            status_code, version = version_1_state.get_status()
            assert status_code == HTTPStatus.OK
            assert version == expected_version


class TestEdgeCases:
    """Tests for edge cases and error conditions"""

    def test_invalid_rollback_version_format(self, version_2_state):
        status_code = version_2_state.rollback_status("invalid")
        assert status_code == HTTPStatus.BAD_REQUEST

        status_code, version = version_2_state.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "2"

    def test_rollback_with_empty_body(self, version_2_state):
        status_code = version_2_state.rollback_status()
        assert status_code == HTTPStatus.OK

        status_code, version = version_2_state.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "1"

    def test_consecutive_major_version_updates(self, version_1_state):
        expected_versions = ["2", "3", "4"]
        for expected_version in expected_versions:
            status_code = version_1_state.rewrite_status()
            assert status_code == HTTPStatus.OK

            status_code, version = version_1_state.get_status()
            assert status_code == HTTPStatus.OK
            assert version == expected_version

    def test_multiple_operations_sequence(self, clean_state, api_client):
        # Set initial version
        status_code = api_client.set_status()
        assert status_code == HTTPStatus.CREATED

        status_code, version = api_client.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "1"

        # Multiple minor updates
        for expected_minor in range(1, 4):
            status_code = api_client.update_status()
            assert status_code == HTTPStatus.OK

            status_code, version = api_client.get_status()
            assert status_code == HTTPStatus.OK
            assert version == f"1.{expected_minor}"

        # Major update
        status_code = api_client.rewrite_status()
        assert status_code == HTTPStatus.OK

        status_code, version = api_client.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "2"

        # More minor updates on new major version
        status_code = api_client.update_status()
        assert status_code == HTTPStatus.OK

        status_code, version = api_client.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "2.1"

        # Rollback to specific version
        status_code = api_client.rollback_status("1.2")
        assert status_code == HTTPStatus.OK

        status_code, version = api_client.get_status()
        assert status_code == HTTPStatus.OK
        assert version == "1.2"

    # Test invalid methods
    def test_invalid_method_for_get_status(self, client):
        response = client.post("/status")
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_invalid_method_for_set_status(self, client):
        response = client.put("/setStatus")
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_invalid_method_for_update_status(self, client):
        response = client.delete("/updateStatus")
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_invalid_method_for_rewrite_status(self, client):
        response = client.get("/rewriteStatus")
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_invalid_method_for_remove_status(self, client):
        response = client.post("/removeStatus")
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_invalid_method_for_rollback_status(self, client):
        response = client.get("/rollbackStatusVersion")
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
