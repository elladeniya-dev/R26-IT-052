from app.database import SessionLocal, engine, Base
from app.models import Product


Base.metadata.create_all(bind=engine)


sample_products = [
    {
        "item_id": "P001",
        "title": "Black Casual Crop Top",
        "category": "top",
        "subcategory": "crop_top",
        "color": ["black"],
        "style": ["casual"],
        "brand": "Gflock",
        "price": 3500,
        "currency": "LKR",
        "image_url": "https://example.com/images/black-crop-top.jpg",
        "product_url": "https://example.com/products/black-crop-top",
        "source": "gflock",
        "description": "Black casual crop top suitable for everyday wear",
        "availability": True
    },
    {
        "item_id": "P002",
        "title": "Blue Denim Jeans",
        "category": "bottom",
        "subcategory": "jeans",
        "color": ["blue"],
        "style": ["casual"],
        "brand": "Kelly Felder",
        "price": 6200,
        "currency": "LKR",
        "image_url": "https://example.com/images/blue-jeans.jpg",
        "product_url": "https://example.com/products/blue-jeans",
        "source": "kelly_felder",
        "description": "Blue denim jeans for casual outfits",
        "availability": True
    },
    {
        "item_id": "P003",
        "title": "White Casual Jacket",
        "category": "outerwear",
        "subcategory": "jacket",
        "color": ["white"],
        "style": ["casual"],
        "brand": "Gflock",
        "price": 7500,
        "currency": "LKR",
        "image_url": "https://example.com/images/white-jacket.jpg",
        "product_url": "https://example.com/products/white-jacket",
        "source": "gflock",
        "description": "White casual jacket suitable for layering",
        "availability": True
    },
    {
        "item_id": "P004",
        "title": "Beige Formal Trousers",
        "category": "bottom",
        "subcategory": "trousers",
        "color": ["beige"],
        "style": ["formal", "office"],
        "brand": "Mimosa",
        "price": 5800,
        "currency": "LKR",
        "image_url": "https://example.com/images/beige-trousers.jpg",
        "product_url": "https://example.com/products/beige-trousers",
        "source": "mimosa",
        "description": "Beige formal trousers for office wear",
        "availability": True
    },
    {
        "item_id": "P005",
        "title": "White Formal Shirt",
        "category": "top",
        "subcategory": "shirt",
        "color": ["white"],
        "style": ["formal", "office"],
        "brand": "Kelly Felder",
        "price": 4900,
        "currency": "LKR",
        "image_url": "https://example.com/images/white-shirt.jpg",
        "product_url": "https://example.com/products/white-shirt",
        "source": "kelly_felder",
        "description": "White formal shirt suitable for office outfits",
        "availability": True
    },
    {
        "item_id": "P006",
        "title": "Black Blazer",
        "category": "outerwear",
        "subcategory": "blazer",
        "color": ["black"],
        "style": ["formal", "office"],
        "brand": "Mimosa",
        "price": 9500,
        "currency": "LKR",
        "image_url": "https://example.com/images/black-blazer.jpg",
        "product_url": "https://example.com/products/black-blazer",
        "source": "mimosa",
        "description": "Black blazer for formal and office outfits",
        "availability": True
    },
    {
        "item_id": "P007",
        "title": "Red Party Dress",
        "category": "dress",
        "subcategory": "party_dress",
        "color": ["red"],
        "style": ["party", "elegant"],
        "brand": "Gflock",
        "price": 8900,
        "currency": "LKR",
        "image_url": "https://example.com/images/red-party-dress.jpg",
        "product_url": "https://example.com/products/red-party-dress",
        "source": "gflock",
        "description": "Red party dress for evening events",
        "availability": True
    },
    {
        "item_id": "P008",
        "title": "Black Elegant Jacket",
        "category": "outerwear",
        "subcategory": "jacket",
        "color": ["black"],
        "style": ["party", "elegant"],
        "brand": "Kelly Felder",
        "price": 7200,
        "currency": "LKR",
        "image_url": "https://example.com/images/black-elegant-jacket.jpg",
        "product_url": "https://example.com/products/black-elegant-jacket",
        "source": "kelly_felder",
        "description": "Black elegant jacket for party outfits",
        "availability": True
    }
]


def seed_products():
    db = SessionLocal()

    try:
        for product_data in sample_products:
            existing_product = db.query(Product).filter(
                Product.item_id == product_data["item_id"]
            ).first()

            if existing_product:
                print(f"Product already exists: {product_data['item_id']}")
            else:
                product = Product(**product_data)
                db.add(product)
                print(f"Inserted product: {product_data['item_id']}")

        db.commit()
        print("Sample product seeding completed successfully.")

    except Exception as e:
        db.rollback()
        print("Error while inserting sample products:")
        print(e)

    finally:
        db.close()


if __name__ == "__main__":
    seed_products()