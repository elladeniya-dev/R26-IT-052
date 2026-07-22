from pathlib import Path
import sys


SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))


def main():
    from app.database import SessionLocal
    from app.outfit_generator import generate_outfits_for_selected_item

    db = SessionLocal()

    try:
        result = generate_outfits_for_selected_item(
            db=db,
            user_id="USR001",
            selected_item_id="P001",
            occasion="casual",
            max_outfits=5,
        )

        print(result)

    finally:
        db.close()


if __name__ == "__main__":
    main()
