import json
import os
import urllib.error
import urllib.request

from fastapi import HTTPException


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

    try:
        with urllib.request.urlopen(endpoint_url, timeout=10) as response:
            response_body = response.read().decode("utf-8")
            data = json.loads(response_body)

    except urllib.error.HTTPError as error:
        raise HTTPException(
            status_code=error.code,
            detail=f"Chala preference API returned an error: {error.reason}",
        )

    except urllib.error.URLError as error:
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to Chala preference API: {error.reason}",
        )

    except TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Chala preference API request timed out",
        )

    return {
        "user_id": data.get("user_id", user_id),
        "categories": data.get("categories", []),
        "colors": data.get("colors", []),
        "styles": data.get("styles", []),
        "occasions": data.get("occasions", []),
        "preferred_brands": data.get("preferred_brands", []),
    }