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
from typing import Any, Dict

GOOGLE_CHAT_WEBHOOK_URL = getenv("GOOGLE_CHAT_WEBHOOK_URL")
SENTRY_DSN = getenv("SENTRY_DSN")

if not GOOGLE_CHAT_WEBHOOK_URL or not SENTRY_DSN:
    raise ValueError(
        "Please make sure that GOOGLE_CHAT_WEBHOOK_URL and SENTRY_DSN are specified in the service.env file."
    )


sentry_sdk.init(
    dsn=SENTRY_DSN,
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

app = FastAPI()


def transform_sentry_webhook_to_google_chat(sentry_payload: Dict[str, Any]) -> Dict[str, str]:
    """Transform Sentry webhook payload into a format suitable for Google Chat."""
    event = sentry_payload.get("event", {})

    return {
        "text": (
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
    logger.info(f"Received webhook: {data}")

    google_chat_message = transform_sentry_webhook_to_google_chat(data)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_CHAT_WEBHOOK_URL,
            json=google_chat_message,
            headers={"Content-Type": "application/json; charset=UTF-8"},
        )

    if response.status_code == 200:
        return {"message": "Webhook received and forwarded to Google Chat successfully"}
    else:
        failed_message = f"Failed to send message to Google Chat: {response.text}"
        logger.error(failed_message)
        return {"error": failed_message}
