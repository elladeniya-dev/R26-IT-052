import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
import os

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


OUTPUT_FILE = Path("output") / "combined_trend_observations.json"


def parse_datetime(value: str):
    if not value:
        return datetime.now()

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now()


def load_json_file(file_path: Path) -> list[dict]:
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Expected JSON file to contain a list of observations")

    return data


def test_database_connection(engine) -> None:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        result.scalar_one()


def insert_trend_observations(engine, observations: list[dict]) -> dict:
    inserted_count = 0
    skipped_count = 0

    insert_query = text("""
        INSERT INTO trend_observations (
            source_name,
            source_type,
            attribute_type,
            attribute_value,
            keyword,
            mention_count,
            rank_position,
            collected_at
        )
        VALUES (
            :source_name,
            :source_type,
            :attribute_type,
            :attribute_value,
            :keyword,
            :mention_count,
            :rank_position,
            :collected_at
        )
    """)

    duplicate_check_query = text("""
        SELECT observation_id
        FROM trend_observations
        WHERE source_name = :source_name
          AND source_type = :source_type
          AND attribute_type = :attribute_type
          AND attribute_value = :attribute_value
          AND keyword = :keyword
          AND collected_at = :collected_at
        LIMIT 1
    """)

    with engine.begin() as connection:
        for observation in observations:
            source_name = observation.get("source_name")
            source_type = observation.get("source_type")
            attribute_type = observation.get("attribute_type")
            attribute_value = observation.get("attribute_value")
            keyword = observation.get("keyword")
            mention_count = observation.get("mention_count", 0)
            rank_position = observation.get("rank_position")
            collected_at = parse_datetime(observation.get("collected_at"))

            if not source_name or not source_type or not attribute_type or not attribute_value:
                skipped_count += 1
                continue

            params = {
                "source_name": source_name,
                "source_type": source_type,
                "attribute_type": attribute_type.lower(),
                "attribute_value": attribute_value.lower(),
                "keyword": keyword,
                "mention_count": mention_count,
                "rank_position": rank_position,
                "collected_at": collected_at,
            }

            existing_record = connection.execute(
                duplicate_check_query,
                params
            ).fetchone()

            if existing_record:
                skipped_count += 1
                continue

            connection.execute(insert_query, params)
            inserted_count += 1

    return {
        "inserted_count": inserted_count,
        "skipped_count": skipped_count,
        "total_records": len(observations),
    }


def main():
    print("Starting trend observation database loader...")

    load_dotenv()

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL not found in .env file")

    print(f"Reading file: {OUTPUT_FILE}")

    observations = load_json_file(OUTPUT_FILE)

    print(f"Observations found in JSON: {len(observations)}")

    engine = create_engine(database_url)

    print("Testing database connection...")
    test_database_connection(engine)
    print("Database connection successful.")

    result = insert_trend_observations(
        engine=engine,
        observations=observations,
    )

    print("\nDatabase loading completed.")
    print(f"Total records in JSON: {result['total_records']}")
    print(f"Inserted records: {result['inserted_count']}")
    print(f"Skipped records: {result['skipped_count']}")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as error:
        print(f"File error: {error}")
    except SQLAlchemyError as error:
        print(f"Database error: {error}")
    except Exception as error:
        print(f"Unexpected error: {error}")