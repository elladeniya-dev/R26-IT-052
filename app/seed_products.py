from app.database import SessionLocal
from app.models.product import Product


sample_products = [
    {
        "item_id": "P002",
        "title": "White Formal Blouse",
        "category": "top",
        "subcategory": "blouse",
        "color": ["white"],
        "style": ["formal", "office"],
        "brand": "Sample Brand",
        "price": 4200,
        "currency": "LKR",
        "image_url": "https://example.com/white-formal-blouse.jpg",
        "product_url": "https://example.com/products/white-formal-blouse",
        "source": "sample_data",
        "description": "White formal blouse suitable for office wear",
        "availability": True
    },
    {
        "item_id": "P003",
        "title": "Blue Denim Jeans",
        "category": "bottom",
        "subcategory": "jeans",
        "color": ["blue"],
        "style": ["casual"],
        "brand": "Sample Brand",
        "price": 6500,
        "currency": "LKR",
        "image_url": "https://example.com/blue-denim-jeans.jpg",
        "product_url": "https://example.com/products/blue-denim-jeans",
        "source": "sample_data",
        "description": "Blue denim jeans for casual outfits",
        "availability": True
    },
    {
        "item_id": "P004",
        "title": "Black Formal Trouser",
        "category": "bottom",
        "subcategory": "trouser",
        "color": ["black"],
        "style": ["formal", "office"],
        "brand": "Sample Brand",
        "price": 5800,
        "currency": "LKR",
        "image_url": "https://example.com/black-formal-trouser.jpg",
        "product_url": "https://example.com/products/black-formal-trouser",
        "source": "sample_data",
        "description": "Black formal trouser suitable for office wear",
        "availability": True
    },
    {
        "item_id": "P005",
        "title": "Beige Casual Jacket",
        "category": "outerwear",
        "subcategory": "jacket",
        "color": ["beige"],
        "style": ["casual"],
        "brand": "Sample Brand",
        "price": 8900,
        "currency": "LKR",
        "image_url": "https://example.com/beige-casual-jacket.jpg",
        "product_url": "https://example.com/products/beige-casual-jacket",
        "source": "sample_data",
        "description": "Beige jacket suitable for casual outfits",
        "availability": True
    },
    {
        "item_id": "P006",
        "title": "Red Party Dress",
        "category": "dress",
        "subcategory": "party_dress",
        "color": ["red"],
        "style": ["party", "elegant"],
        "brand": "Sample Brand",
        "price": 12000,
        "currency": "LKR",
        "image_url": "https://example.com/red-party-dress.jpg",
        "product_url": "https://example.com/products/red-party-dress",
        "source": "sample_data",
        "description": "Red elegant party dress",
        "availability": True
    }
]


def seed_products():
    db = SessionLocal()

    try:
        inserted_count = 0

        for product_data in sample_products:
            existing_product = db.query(Product).filter(
                Product.item_id == product_data["item_id"]
            ).first()

            if existing_product:
                print(f"Skipped {product_data['item_id']} - already exists")
                continue

            product = Product(**product_data)
            db.add(product)
            inserted_count += 1

        db.commit()
        print(f"Inserted {inserted_count} new products successfully")

    except Exception as e:
        db.rollback()
        print(f"Error while inserting products: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_products()