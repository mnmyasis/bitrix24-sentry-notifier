import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport


with patch("sentry_sdk.init") as mock_sentry_init:
    from app.main import app, transform_sentry_webhook_to_google_chat


@pytest.fixture(autouse=True)
def mock_environment(monkeypatch):
    monkeypatch.setenv("BITRIX24_WEBHOOK_URL", "MOCK_URL")
    monkeypatch.setenv("SENTRY_DSN", "MOCK_SENTRY_DSN")
    monkeypatch.setenv("ALLOWED_ENVIRONMENTS", "production,prod")


@pytest_asyncio.fixture
async def async_test_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def mock_http_client():
    with patch("httpx.AsyncClient") as mock:
        mock_instance = AsyncMock()
        mock_instance.post.return_value = MagicMock(status_code=200)
        mock.return_value.__aenter__.return_value = mock_instance
        yield mock_instance


VALID_PAYLOAD = {
    "id": "12345",
    "project_name": "test-project",
    "level": "error",
    "culprit": "test.views",
    "message": "Test error",
    "url": "http://test.com",
    "event": {"environment": "production", "platform": "python"},
}


@pytest.mark.asyncio
class TestWebhookHandler:
    async def test_successful_processing(self, async_test_client, mock_http_client):
        response = await async_test_client.post("/sentry-webhook", json=VALID_PAYLOAD)

        assert response.status_code == 200
        assert "successfully" in response.json()["message"]
        mock_http_client.post.assert_called_once()

    async def test_non_production_environment(
        self, async_test_client, mock_http_client
    ):
        test_payload = {**VALID_PAYLOAD, "event": {"environment": "development"}}

        response = await async_test_client.post("/sentry-webhook", json=test_payload)

        assert response.status_code == 200
        assert "Skipping notification" in response.json()["message"]
        mock_http_client.post.assert_not_called()


class TestPayloadTransformation:
    def test_valid_transformation(self):
        result = transform_sentry_webhook_to_google_chat(VALID_PAYLOAD)
        assert isinstance(result, dict)
        assert "*Level*: error" in result["text"]
        assert "*URL*: http://test.com" in result["text"]

    def test_invalid_payload(self):
        """
        Проверка обработки невалидного payload.
        """
        assert transform_sentry_webhook_to_google_chat({}) is None


@pytest.mark.asyncio
class TestHealthChecks:
    async def test_health_check_endpoint(self, async_test_client):
        for method in [async_test_client.get, async_test_client.head]:
            response = await method("/health-check")
            assert response.status_code == 204
