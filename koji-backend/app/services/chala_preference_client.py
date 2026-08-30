import json
import os
import socket
import time
import urllib.error
import urllib.request

from fastapi import HTTPException


CHALA_API_FIRST_TIMEOUT_SECONDS = 70
CHALA_API_RETRY_TIMEOUT_SECONDS = 35
CHALA_API_RETRY_WAIT_SECONDS = 3
RETRYABLE_HTTP_STATUS_CODES = {502, 503, 504}


def _is_timeout_error(error):
    error_text = str(error).lower()
    reason = getattr(error, "reason", None)

    return (
        isinstance(error, TimeoutError)
        or isinstance(error, socket.timeout)
        or isinstance(reason, TimeoutError)
        or isinstance(reason, socket.timeout)
        or "timed out" in error_text
        or "timeout" in error_text
    )


def _fetch_chala_preferences(endpoint_url: str, timeout_seconds: int):
    request = urllib.request.Request(
        endpoint_url,
        headers={
            "Accept": "application/json",
            "User-Agent": "OutfitIQ-Koji-Backend/1.0",
        },
    )

    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        response_body = response.read().decode("utf-8")
        return json.loads(response_body)


def get_chala_enriched_preferences(user_id: int):
    chala_api_url = os.getenv("CHALA_API_URL")

    if not chala_api_url:
        raise HTTPException(
            status_code=500,
            detail="CHALA_API_URL is not configured in .env",
        )

    endpoint_url = (
        f"{chala_api_url.rstrip('/')}"
        f"/integration/users/{user_id}/enriched-preferences"
    )

    timeout_attempts = [
        CHALA_API_FIRST_TIMEOUT_SECONDS,
        CHALA_API_RETRY_TIMEOUT_SECONDS,
    ]

    last_error = None

    for attempt_index, timeout_seconds in enumerate(timeout_attempts, start=1):
        try:
            data = _fetch_chala_preferences(
                endpoint_url=endpoint_url,
                timeout_seconds=timeout_seconds,
            )

            return {
                "user_id": data.get("user_id", user_id),
                "categories": data.get("categories", []),
                "colors": data.get("colors", []),
                "styles": data.get("styles", []),
                "occasions": data.get("occasions", []),
                "preferred_brands": data.get("preferred_brands", []),
            }

        except urllib.error.HTTPError as error:
            last_error = error

            if (
                error.code in RETRYABLE_HTTP_STATUS_CODES
                and attempt_index < len(timeout_attempts)
            ):
                time.sleep(CHALA_API_RETRY_WAIT_SECONDS)
                continue

            raise HTTPException(
                status_code=error.code,
                detail=(
                    "Chala preference API returned an error: "
                    f"{error.reason}"
                ),
            )

        except urllib.error.URLError as error:
            last_error = error

            if attempt_index < len(timeout_attempts):
                time.sleep(CHALA_API_RETRY_WAIT_SECONDS)
                continue

            status_code = 504 if _is_timeout_error(error) else 503

            raise HTTPException(
                status_code=status_code,
                detail=(
                    "Could not connect to Chala preference API after retry. "
                    "Chala Render service may still be waking up. "
                    f"Original error: {error.reason}"
                ),
            )

        except (TimeoutError, socket.timeout) as error:
            last_error = error

            if attempt_index < len(timeout_attempts):
                time.sleep(CHALA_API_RETRY_WAIT_SECONDS)
                continue

            raise HTTPException(
                status_code=504,
                detail=(
                    "Chala preference API request timed out after retry. "
                    "Chala Render service may still be waking up. "
                    "Please try again."
                ),
            )

        except json.JSONDecodeError:
            raise HTTPException(
                status_code=502,
                detail="Chala preference API returned invalid JSON.",
            )

    raise HTTPException(
        status_code=503,
        detail=f"Could not fetch Chala preferences. Last error: {last_error}",
    )