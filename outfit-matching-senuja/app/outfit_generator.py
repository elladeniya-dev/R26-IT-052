from typing import List, Dict, Optional
from itertools import product as cartesian_product

from sqlalchemy.orm import Session

from app.models import Product
from app.compatibility import calculate_compatibility_score


def product_to_dict(product: Product) -> Dict:
    """
    Converts a SQLAlchemy Product object into a normal Python dictionary.
    This makes it easier to use inside scoring and API response.
    """
    return {
        "item_id": product.item_id,
        "title": product.title,
        "category": product.category,
        "subcategory": product.subcategory,
        "color": product.color,
        "style": product.style,
        "brand": product.brand,
        "price": product.price,
        "currency": product.currency,
        "image_url": product.image_url,
        "product_url": product.product_url,
    }


def get_available_products_by_category(
    db: Session,
    category: str,
    exclude_item_id: Optional[str] = None
) -> List[Product]:
    """
    Reads available products by category from the products table.
    Example:
    category = bottom → returns all available bottoms.
    """
    query = db.query(Product).filter(
        Product.category == category,
        Product.availability == True
    )

    if exclude_item_id:
        query = query.filter(Product.item_id != exclude_item_id)

    return query.all()


def get_required_categories(selected_category: str) -> Dict:
    """
    Decides what item categories are needed based on selected item category.

    Example:
    selected top → need bottom, optional outerwear
    selected dress → optional outerwear
    """
    selected_category = selected_category.lower()

    if selected_category == "top":
        return {
            "required": ["bottom"],
            "optional": ["outerwear"]
        }

    if selected_category == "bottom":
        return {
            "required": ["top"],
            "optional": ["outerwear"]
        }

    if selected_category == "dress":
        return {
            "required": [],
            "optional": ["outerwear"]
        }

    if selected_category == "outerwear":
        return {
            "required": ["top", "bottom"],
            "optional": []
        }

    return {
        "required": [],
        "optional": []
    }


def build_basic_outfit_items(
    selected_item: Dict,
    required_product_groups: List[List[Product]]
) -> List[List[Dict]]:
    """
    Builds basic outfits using selected item + required category items.

    Example:
    selected top + all bottoms
    selected outerwear + all tops + all bottoms
    """
    outfits = []

    if not required_product_groups:
        outfits.append([selected_item])
        return outfits

    for product_combination in cartesian_product(*required_product_groups):
        outfit_items = [selected_item]

        for product_item in product_combination:
            outfit_items.append(product_to_dict(product_item))

        outfits.append(outfit_items)

    return outfits


def add_optional_items_to_outfits(
    basic_outfits: List[List[Dict]],
    optional_products: List[Product]
) -> List[List[Dict]]:
    """
    Adds optional items to outfits.

    Example:
    selected top + bottom
    selected top + bottom + outerwear

    This keeps both versions:
    - without optional item
    - with optional item
    """
    final_outfits = []

    for outfit in basic_outfits:
        final_outfits.append(outfit)

        for optional_product in optional_products:
            outfit_with_optional = outfit.copy()
            outfit_with_optional.append(product_to_dict(optional_product))
            final_outfits.append(outfit_with_optional)

    return final_outfits


def generate_outfits_for_selected_item(
    db: Session,
    user_id: str,
    selected_item_id: str,
    occasion: str,
    max_outfits: int
) -> Dict:
    """
    Main outfit generation function.

    Steps:
    1. Find selected item
    2. Decide required and optional categories
    3. Generate outfit combinations
    4. Calculate compatibility score
    5. Rank highest score outfits
    6. Return response
    """

    selected_product = db.query(Product).filter(
        Product.item_id == selected_item_id,
        Product.availability == True
    ).first()

    if not selected_product:
        return {
            "success": False,
            "message": "Selected item not found or unavailable",
            "outfits": []
        }

    selected_item = product_to_dict(selected_product)
    selected_category = selected_item["category"]

    category_rules = get_required_categories(selected_category)

    required_product_groups = []

    for category in category_rules["required"]:
        products = get_available_products_by_category(
            db=db,
            category=category,
            exclude_item_id=selected_item_id
        )

        if not products:
            return {
                "success": False,
                "message": f"No available products found for required category: {category}",
                "outfits": []
            }

        required_product_groups.append(products)

    optional_products = []

    for category in category_rules["optional"]:
        products = get_available_products_by_category(
            db=db,
            category=category,
            exclude_item_id=selected_item_id
        )

        optional_products.extend(products)

    basic_outfits = build_basic_outfit_items(
        selected_item=selected_item,
        required_product_groups=required_product_groups
    )

    all_outfits = add_optional_items_to_outfits(
        basic_outfits=basic_outfits,
        optional_products=optional_products
    )

    scored_outfits = []

    for index, outfit_items in enumerate(all_outfits, start=1):
        score_result = calculate_compatibility_score(
            outfit_items=outfit_items,
            occasion=occasion
        )

        outfit = {
            "outfit_id": f"OUT{index:03d}",
            "items": [
                {
                    "item_id": item["item_id"],
                    "title": item["title"],
                    "role": item["category"],
                    "color": item["color"],
                    "style": item["style"],
                    "image_url": item["image_url"],
                    "product_url": item["product_url"],
                    "price": item["price"],
                    "brand": item["brand"],
                }
                for item in outfit_items
            ],
            "compatibility_score": score_result["compatibility_score"],
            "reason_tags": score_result["reason_tags"],
            "score_breakdown": score_result["score_breakdown"]
        }

        scored_outfits.append(outfit)

    ranked_outfits = sorted(
        scored_outfits,
        key=lambda outfit: outfit["compatibility_score"],
        reverse=True
    )

    return {
        "success": True,
        "message": "Outfits generated successfully",
        "user_id": user_id,
        "selected_item_id": selected_item_id,
        "outfits": ranked_outfits[:max_outfits]
    }