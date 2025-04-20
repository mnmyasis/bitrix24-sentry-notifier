# Sentry to Google Chat Webhook Notifier

This is a FastAPI application designed to process webhooks from Sentry, transform them into a format suitable for Google Chat, and send notifications to a specified Google Chat Space. The application also includes a health-check endpoint to verify API status.

## Key Features

1. **Sentry Webhook Processing**:

   - The app receives webhooks from Sentry, validates their content, and filters based on allowed environments (e.g., `production`, `prod`).
   - Transforms webhook data into a format compatible with Google Chat.

2. **Google Chat Notifications**:

   - Notifications are sent via a Google Chat webhook.
   - If the environment is not allowed, the notification is skipped.

3. **Health Check Endpoint**:

   - Includes a `/health-check` endpoint to verify the API's operational status.

4. **Sentry Integration**:
   - The app uses Sentry SDK for error tracking within the service itself.

---

## Requirements

To run the application, you will need:

- Docker and Docker Compose

---

## Setup

### 1. Environment Variables

Create a `.env.test` (or `.env` for production) file and add the following variables:

```env
GOOGLE_CHAT_WEBHOOK_URL=your_google_chat_webhook_url
SENTRY_DSN=your_sentry_dsn_for_error_tracking
ALLOWED_ENVIRONMENTS=production,prod
```

- `GOOGLE_CHAT_WEBHOOK_URL`: The Google Chat webhook URL where notifications will be sent.
- `SENTRY_DSN`: The DSN for Sentry integration.
- `ALLOWED_ENVIRONMENTS`: A comma-separated list of environments for which notifications are allowed.

### 2. Installing Dependencies

Ensure all dependencies are installed. You can install them locally or use Docker.

```bash
pip install -r requirements.txt
pip install -r requirements-test.txt
```

---

## Running the Application

### Local Run

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Start the application:

   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

3. Verify the health-check endpoint:
   - Open your browser and navigate to: `http://localhost:8000/health-check`.

### Running with Docker

1. Build and start the containers:

   ```bash
   docker compose up -d --build webhook-service
   ```

2. The application will be available at: `http://localhost:8007`.

---

## Testing

Tests are written using `pytest` and `pytest-asyncio`. To run the tests:

```bash
docker compose run --rm tests
```

Or locally:

```bash
pytest -v tests/
```

The `pytest.ini` file ensures compatibility with `pytest-asyncio` by setting the asyncio mode to `strict` and configuring the fixture loop scope.

---

## API Endpoints

### 1. POST `/sentry-webhook`

Accepts a webhook from Sentry.

- **Request Body**: JSON object containing webhook data.
- **Response**:
  - `200 OK`: Successful processing.
  - Example response:

    ```json
    {
      "message": "Webhook received and forwarded to Google Chat successfully"
    }
    ```

### 2. GET/HEAD `/health-check`

Verifies the API's operational status.

- **Response**:
  - `204 No Content`: The service is operational.

---

## Logging

The application uses the `loguru` library for logging. All errors and important events are logged.

---

## Project Structure

```bash
.
├── app/
│   └── main.py           # Main application file
├── tests/
│   └── test_stateless.py # Tests
├── .env.test             # Environment variables for testing
├── .dockerignore         # Files to ignore during Docker builds
├── .gitignore            # Files to ignore in VCS
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile            # Dockerfile for the application
├── Dockerfile.test       # Dockerfile for testing
├── pytest.ini            # Pytest configuration
├── ruff.toml             # Ruff linter configuration
├── requirements.txt      # Application dependencies
└── requirements-test.txt # Test dependencies
```
