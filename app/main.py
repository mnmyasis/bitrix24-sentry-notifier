"""
FastAPI application for processing Sentry webhooks and sending notifications to Google Chat.

This module provides an API that receives webhooks from Sentry, transforms them into a format suitable for Google Chat,
and sends messages to a specified Google Chat channel. The application also includes an endpoint for API health checks.
"""

from fastapi import FastAPI, Request, Response, status
import httpx
from loguru import logger
import sentry_sdk

from os import getenv
from typing import Any, Dict, Optional

BITRIX24_WEBHOOK_URL = getenv("BITRIX24_WEBHOOK_URL")
BITRIX24_DIALOG_ID = getenv("BITRIX24_DIALOG_ID")
SENTRY_DSN = getenv("SENTRY_DSN")
ALLOWED_ENVIRONMENTS = getenv("ALLOWED_ENVIRONMENTS", "production,prod").split(",")

if not BITRIX24_WEBHOOK_URL or not SENTRY_DSN:
    raise ValueError(
        "Please make sure that BITRIX24_WEBHOOK_URL and SENTRY_DSN are specified in the service.env file."
    )


def init_sentry() -> None:
    """Initialize Sentry SDK for error tracking."""
    if not hasattr(init_sentry, "_called"):
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
        )
        init_sentry._called = True


init_sentry()

app = FastAPI()


def transform_sentry_webhook_to_google_chat(
        sentry_payload: Dict[str, Any],
) -> Optional[Dict[str, str]]:
    """Transform Sentry webhook payload into a format suitable for Bitrix24."""
    event = sentry_payload.get("event", {})
    environment = event.get("environment", "").lower().strip()
    if environment not in ALLOWED_ENVIRONMENTS:
        return None

    return {
        "DIALOG_ID": BITRIX24_DIALOG_ID,
        "MESSAGE": (
            f"*ID*: {sentry_payload.get('id')}\n"
            f"*Project*: {sentry_payload.get('project_name')}\n"
            f"*Environment*: {event.get('environment')}\n"
            f"*Level*: {sentry_payload.get('level')}\n"
            f"*Culprit*: {sentry_payload.get('culprit')}\n"
            f"*Message*: {sentry_payload.get('message')}\n"
            f"*Platform*: {event.get('platform', 'unknown')}\n"
            f"*URL*: {sentry_payload.get('url')}"
        )
    }


@app.head(
    "/health-check",
    description="API health check service route",
    status_code=status.HTTP_204_NO_CONTENT,
)
@app.get(
    "/health-check",
    description="API health check service route",
    status_code=status.HTTP_204_NO_CONTENT,
)
def health_check() -> Response:
    """Check API health."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/sentry-webhook")
async def receive_sentry_webhook(request: Request):
    """Process a Sentry webhook."""
    data = await request.json()

    bitrix_message = transform_sentry_webhook_to_google_chat(data)
    if not bitrix_message:
        return {"message": "Environment not allowed. Skipping notification."}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                BITRIX24_WEBHOOK_URL,
                json=bitrix_message,
                headers={"Content-Type": "application/json; charset=UTF-8"},
            )
    except httpx.RequestError as exc:
        logger.error(
            f"An error occurred while sending the message to Bitrix24: {exc}"
        )
        logger.info(f"Received webhook: {data}")

    if response.status_code == 200:
        return {"message": "Webhook received and forwarded to Bitrix24 successfully"}
    else:
        failed_message = f"Failed to send message to Bitrix24: {response.text}"
        logger.error(failed_message)
        return {"error": failed_message}
