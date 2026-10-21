import re
from typing import List, Dict, Optional
from itertools import product as cartesian_product

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.s_models import Product
from app.s_compatibility import calculate_compatibility_score
from app.s_ml_predictor import calculate_outfit_ml_score
from app.s_product_filters import apply_real_product_filter


CATEGORY_ALIASES = {
    "bottom": [
        "bottom",
        "pants",
        "pant",
        "jeans",
        "leggings",
        "legging",
        "skirt",
        "skort",
        "shorts",
    ],
    "outerwear": [
        "outerwear",
        "blazer",
        "jacket",
        "hoodie",
    ],
    "dress": [
        "dress",
        "jumpsuit",
        "romper",
        "set",
    ],
}

# Some crawled catalogs mislabel pants as blazers/tops (e.g. "Flared Leg Formal
# Pant" filed under blazer). When the title names only a bottom garment, trust
# the title over the label so such items are never used as outerwear or tops.
BOTTOM_TITLE_PATTERN = re.compile(
    r"\b(?:pants?|trousers?|jeans?|joggers?|skirts?|skorts?"
    r"|shorts?(?!\s+sleeve)|leggings?)\b",
    re.IGNORECASE,
)
NON_BOTTOM_TITLE_PATTERN = re.compile(
    r"\b(?:blazers?|jackets?|coats?|hoodies?|tops?|tees?|t-?shirts?|shirts?"
    r"|blouses?|tanks?|bodysuits?|sweaters?|cardigans?|dress(?:es)?|jumpsuits?"
    r"|rompers?|sets?|suits?)\b",
    re.IGNORECASE,
)
# Postgres regex for the same words (a permissive pre-filter; the Python
# check above stays the source of truth).
BOTTOM_TITLE_SQL_REGEX = r"\m(pants?|trousers?|jeans?|joggers?|skirts?|skorts?|shorts?|leggings?)\M"


def title_names_only_a_bottom(title: Optional[str]) -> bool:
    text = title or ""
    return bool(BOTTOM_TITLE_PATTERN.search(text)) and not NON_BOTTOM_TITLE_PATTERN.search(text)


MAX_OPTIONAL_PRODUCTS_PER_CATEGORY = 2
MAX_BASIC_OUTFITS_TO_SCORE = 60
MAX_CANDIDATE_OUTFITS_TO_SCORE = 500


def normalize_category(
    category: Optional[str],
    subcategory: Optional[str] = None,
    title: Optional[str] = None,
) -> str:
    """
    Converts crawler-specific categories into outfit-engine categories.
    """
    if title_names_only_a_bottom(title):
        return "bottom"

    cleaned_category = (category or "").strip().lower()
    values_to_check = [
        cleaned_category,
        (subcategory or "").strip().lower(),
    ]

    for value in values_to_check:
        for normalized_category, aliases in CATEGORY_ALIASES.items():
            if value in aliases:
                return normalized_category

    searchable_title = f" {(title or '').strip().lower()} "
    for normalized_category, aliases in CATEGORY_ALIASES.items():
        for alias in aliases:
            if f" {alias} " in searchable_title:
                return normalized_category

    return cleaned_category


def normalize_product_category(product: Product) -> str:
    return normalize_category(
        category=product.category,
        subcategory=product.subcategory,
        title=product.title,
    )


def get_category_query_values(category: str) -> List[str]:
    normalized_category = normalize_category(category)
    return CATEGORY_ALIASES.get(normalized_category, [normalized_category])


def product_to_dict(product: Product) -> Dict:
    """
    Converts a SQLAlchemy Product object into a normal Python dictionary.
    """
    return {
        "item_id": product.item_id,
        "title": product.title,
        "category": normalize_product_category(product),
        "subcategory": product.subcategory,
        "color": product.color,
        "style": product.style,
        "brand": product.brand,
        "price": product.price,
        "currency": product.currency,
        "image_url": product.image_url,
        "product_url": product.product_url,
        "image_embedding": product.image_embedding,
    }


def normalize_list(values) -> List[str]:
    """
    Converts list or string values into lowercase list.
    """
    if not values:
        return []

    if isinstance(values, str):
        return [values.strip().lower()]

    return [str(value).strip().lower() for value in values]


def product_matches_preferred_colors(
    product: Product,
    preferred_colors: Optional[List[str]]
) -> bool:
    """
    Checks whether product color matches preferred colors.
    If no preferred colors are given, all colors are accepted.
    """
    if not preferred_colors:
        return True

    product_colors = normalize_list(product.color)
    preferred_colors = normalize_list(preferred_colors)

    for color in product_colors:
        if color in preferred_colors:
            return True

    return False


def append_unique_products(
    products: List[Product],
    candidates: List[Product],
    max_items: int
) -> List[Product]:
    seen_item_ids = {product.item_id for product in products}

    for candidate in candidates:
        if candidate.item_id in seen_item_ids:
            continue

        products.append(candidate)
        seen_item_ids.add(candidate.item_id)

        if len(products) >= max_items:
            break

    return products


def build_category_query(
    db: Session,
    category: str,
    exclude_item_id: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
):
    category_query_values = get_category_query_values(category)
    category_conditions = [
        Product.category.in_(category_query_values),
        Product.subcategory.in_(category_query_values),
    ]
    if normalize_category(category) == "bottom":
        # Also find bottoms that were filed under another category.
        category_conditions.append(Product.title.op("~*")(BOTTOM_TITLE_SQL_REGEX))

    query = apply_real_product_filter(db.query(Product)).filter(
        or_(*category_conditions),
        Product.availability == True
    )

    if exclude_item_id:
        query = query.filter(Product.item_id != exclude_item_id)

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    return query


def get_available_products_by_category(
    db: Session,
    category: str,
    exclude_item_id: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    preferred_colors: Optional[List[str]] = None,
    max_items_per_category: int = 10,
    color_filter_mismatches: Optional[List[str]] = None,
) -> List[Product]:
    """
    Reads available products by category from the products table.

    Filters:
    - min_price
    - max_price
    - preferred_colors
    - max_items_per_category
    """

    candidate_pool_size = max(max_items_per_category * 12, 100)
    query = build_category_query(
        db=db,
        category=category,
        exclude_item_id=exclude_item_id,
        min_price=min_price,
        max_price=max_price,
    )

    normalized_category = normalize_category(category)
    products = [
        product for product in query.limit(candidate_pool_size).all()
        if normalize_product_category(product) == normalized_category
    ]

    filtered_products = [
        product for product in products
        if product_matches_preferred_colors(
            product=product,
            preferred_colors=preferred_colors
        )
    ]

    if preferred_colors and products and not filtered_products:
        if color_filter_mismatches is not None and category not in color_filter_mismatches:
            color_filter_mismatches.append(category)

    if filtered_products:
        selected_products = filtered_products[:max_items_per_category]
    elif preferred_colors:
        selected_products = []
    else:
        selected_products = products[:max_items_per_category]

    if len(selected_products) < max_items_per_category:
        fallback_products = [
            product for product in build_category_query(
                db=db,
                category=category,
                exclude_item_id=exclude_item_id,
                min_price=min_price,
                max_price=max_price,
            ).limit(candidate_pool_size).all()
            if (
                normalize_product_category(product) == normalized_category
                and product_matches_preferred_colors(product, preferred_colors)
            )
        ]
        selected_products = append_unique_products(
            products=selected_products,
            candidates=fallback_products,
            max_items=max_items_per_category,
        )

    return selected_products


def rank_candidate_products(
    selected_item: Dict,
    products: List[Product],
    occasion: str,
    max_items: int
) -> List[Product]:
    """
    Ranks products before outfit generation using a lightweight pair score.

    This keeps the cartesian product step focused on items that already look
    compatible with the selected clothing item.
    """
    scored_products = []

    for product in products:
        product_dict = product_to_dict(product)
        pair_result = calculate_compatibility_score(
            outfit_items=[selected_item, product_dict],
            occasion=occasion
        )
        scored_products.append(
            (
                pair_result["compatibility_score"],
                product.price or 0,
                product.item_id,
                product
            )
        )

    scored_products.sort(
        key=lambda scored_product: (
            scored_product[0],
            -scored_product[1],
            scored_product[2]
        ),
        reverse=True
    )

    return [
        scored_product[3]
        for scored_product in scored_products[:max_items]
    ]


def get_required_categories(selected_category: str) -> Dict:
    """
    Decides what item categories are needed based on selected item category.
    """
    selected_category = normalize_category(selected_category)

    if selected_category == "top":
        return {
            "required": ["bottom"],
            "optional": ["outerwear", "footwear", "accessory"]
        }

    if selected_category == "bottom":
        return {
            "required": ["top"],
            "optional": ["outerwear", "footwear", "accessory"]
        }

    if selected_category == "dress":
        return {
            "required": [],
            "optional": ["outerwear", "footwear", "accessory"]
        }

    if selected_category == "outerwear":
        return {
            "required": ["top", "bottom"],
            "optional": ["footwear", "accessory"]
        }

    if selected_category == "footwear":
        return {
            "required": ["top", "bottom"],
            "optional": ["outerwear", "accessory"]
        }

    if selected_category == "accessory":
        return {
            "required": ["top", "bottom"],
            "optional": ["outerwear", "footwear"]
        }

    return {
        "required": [],
        "optional": []
    }


def apply_excluded_categories(
    category_rules: Dict,
    excluded_categories: Optional[List[str]]
) -> Dict:
    """
    Removes categories that the user wants to exclude.

    Optional categories can be removed safely.
    Required categories are also removed if user explicitly excludes them,
    but this may make outfit generation fail if no complete outfit can be formed.
    """

    if not excluded_categories:
        return category_rules

    excluded_categories = normalize_list(excluded_categories)

    required_categories = category_rules["required"]
    optional_categories = category_rules["optional"]

    filtered_required_categories = [
        category for category in required_categories
        if category not in excluded_categories
    ]

    filtered_optional_categories = [
        category for category in optional_categories
        if category not in excluded_categories
    ]

    return {
        "required": filtered_required_categories,
        "optional": filtered_optional_categories
    }


def build_basic_outfit_items(
    selected_item: Dict,
    required_product_groups: List[List[Product]]
) -> List[List[Dict]]:
    """
    Builds basic outfits using selected item + required category items.
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
    optional_product_groups: List[List[Product]],
    max_candidates: int = MAX_CANDIDATE_OUTFITS_TO_SCORE,
) -> List[List[Dict]]:
    """
    Builds bounded optional-item combinations across distinct categories.

    Keeps the base outfit, single optional categories, and multi-category
    combinations while limiting candidate scoring work.
    """
    if not basic_outfits or max_candidates <= 0:
        return []

    optional_product_groups = [
        products for products in optional_product_groups if products
    ]
    choice_groups = [
        [None, *products[:MAX_OPTIONAL_PRODUCTS_PER_CATEGORY]]
        for products in optional_product_groups
    ]
    optional_combinations = list(cartesian_product(*choice_groups))
    optional_combinations.sort(
        key=lambda combination: (
            sum(
                product is not None and product is not group[0]
                for group, product in zip(optional_product_groups, combination)
            ),
            sum(product is not None for product in combination),
        )
    )

    final_outfits = []
    for optional_combination in optional_combinations:
        for outfit in basic_outfits:
            outfit_with_optional = outfit.copy()
            outfit_with_optional.extend(
                product_to_dict(optional_product)
                for optional_product in optional_combination
                if optional_product is not None
            )
            final_outfits.append(outfit_with_optional)

            if len(final_outfits) >= max_candidates:
                return final_outfits

    return final_outfits


def deduplicate_outfit_items(outfits: List[List[Dict]]) -> List[List[Dict]]:
    unique_outfits = []
    seen_item_sets = set()

    for outfit in outfits:
        item_set = tuple(sorted(item["item_id"] for item in outfit))

        if item_set in seen_item_sets:
            continue

        seen_item_sets.add(item_set)
        unique_outfits.append(outfit)

    return unique_outfits


def get_diversity_categories(selected_category: str) -> List[str]:
    selected_category = normalize_category(selected_category)

    if selected_category == "top":
        return ["bottom"]

    if selected_category == "bottom":
        return ["top"]

    if selected_category == "dress":
        return ["outerwear", "footwear", "accessory"]

    if selected_category in {"outerwear", "footwear", "accessory"}:
        return ["top", "bottom"]

    return []


def get_outfit_diversity_key(
    outfit: Dict,
    selected_item_id: str,
    diversity_categories: List[str],
) -> tuple:
    key_items = [
        (item["role"], item["item_id"])
        for item in outfit["items"]
        if (
            item["item_id"] != selected_item_id
            and item["role"] in diversity_categories
        )
    ]

    if key_items:
        return tuple(key_items)

    return tuple(
        (item["role"], item["item_id"])
        for item in outfit["items"]
        if item["item_id"] != selected_item_id
    )


def diversify_ranked_outfits(
    ranked_outfits: List[Dict],
    selected_category: str,
    selected_item_id: str,
    max_outfits: int,
) -> List[Dict]:
    diversity_categories = get_diversity_categories(selected_category)
    selected_outfits = []
    seen_diversity_keys = set()
    seen_item_sets = set()

    for outfit in ranked_outfits:
        diversity_key = get_outfit_diversity_key(
            outfit=outfit,
            selected_item_id=selected_item_id,
            diversity_categories=diversity_categories,
        )
        item_set = tuple(sorted(item["item_id"] for item in outfit["items"]))

        if diversity_key in seen_diversity_keys:
            continue

        selected_outfits.append(outfit)
        seen_diversity_keys.add(diversity_key)
        seen_item_sets.add(item_set)

        if len(selected_outfits) >= max_outfits:
            return selected_outfits

    for outfit in ranked_outfits:
        item_set = tuple(sorted(item["item_id"] for item in outfit["items"]))

        if item_set in seen_item_sets:
            continue

        selected_outfits.append(outfit)
        seen_item_sets.add(item_set)

        if len(selected_outfits) >= max_outfits:
            break

    return selected_outfits


def calculate_hybrid_score(
    outfit_items: List[Dict],
    occasion: str
) -> Dict:
    """
    Combines rule-based compatibility score and ML compatibility score.

    Formula:
    final_score = 0.70 * rule_based_score + 0.30 * ml_score
    """

    rule_result = calculate_compatibility_score(
        outfit_items=outfit_items,
        occasion=occasion
    )

    rule_based_score = rule_result["compatibility_score"]

    ml_score = calculate_outfit_ml_score(outfit_items)
    ml_available = ml_score is not None

    final_score = (
        0.70 * rule_based_score + 0.30 * ml_score
        if ml_available
        else rule_based_score
    )
    reason_tags = list(rule_result["reason_tags"])

    if ml_available:
        reason_tags.append("ML compatibility score applied")

    return {
        "compatibility_score": round(final_score, 2),
        "rule_based_score": round(rule_based_score, 2),
        "ml_score": round(ml_score, 2) if ml_available else None,
        "ml_available": ml_available,
        "reason_tags": reason_tags,
        "score_breakdown": {
            "style_match_score": rule_result["score_breakdown"]["style_match_score"],
            "color_match_score": rule_result["score_breakdown"]["color_match_score"],
            "category_match_score": rule_result["score_breakdown"]["category_match_score"],
            "occasion_match_score": rule_result["score_breakdown"]["occasion_match_score"],
            "rule_based_score": round(rule_based_score, 2),
            "ml_score": round(ml_score, 2) if ml_available else None,
            "ml_available": ml_available,
            "final_hybrid_score": round(final_score, 2)
        }
    }


def generate_outfits_for_selected_item(
    db: Session,
    user_id: str,
    selected_item_id: str,
    occasion: str,
    max_outfits: int,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    preferred_colors: Optional[List[str]] = None,
    excluded_categories: Optional[List[str]] = None,
    max_items_per_category: int = 10
) -> Dict:
    """
    Main outfit generation function.

    Steps:
    1. Find selected item
    2. Decide required and optional categories
    3. Apply filters
    4. Generate outfit combinations
    5. Calculate rule-based score
    6. Calculate ML score
    7. Combine both scores
    8. Rank outfits
    """

    selected_product = apply_real_product_filter(db.query(Product)).filter(
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

    if not category_rules["required"] and not category_rules["optional"]:
        return {
            "success": False,
            "message": f"Unsupported selected item category: {selected_category}",
            "outfits": []
        }

    category_rules = apply_excluded_categories(
        category_rules=category_rules,
        excluded_categories=excluded_categories
    )
    product_fetch_limit = max(max_items_per_category, max_outfits)

    required_product_groups = []
    color_filter_mismatches = []

    for category in category_rules["required"]:
        products = get_available_products_by_category(
            db=db,
            category=category,
            exclude_item_id=selected_item_id,
            min_price=min_price,
            max_price=max_price,
            preferred_colors=preferred_colors,
            max_items_per_category=product_fetch_limit,
            color_filter_mismatches=color_filter_mismatches,
        )

        if not products:
            if category in color_filter_mismatches:
                selected_colors = ", ".join(preferred_colors or [])
                message = (
                    f"No available {category} products match your selected colors "
                    f"({selected_colors}) within the selected price range."
                )
            else:
                message = (
                    "No available products found for required category after "
                    f"applying filters: {category}"
                )
            return {
                "success": False,
                "message": message,
                "outfits": []
            }

        products = rank_candidate_products(
            selected_item=selected_item,
            products=products,
            occasion=occasion,
            max_items=product_fetch_limit
        )

        required_product_groups.append(products)

    optional_product_groups = []

    for category in category_rules["optional"]:
        products = get_available_products_by_category(
            db=db,
            category=category,
            exclude_item_id=selected_item_id,
            min_price=min_price,
            max_price=max_price,
            preferred_colors=preferred_colors,
            max_items_per_category=product_fetch_limit,
            color_filter_mismatches=color_filter_mismatches,
        )

        products = rank_candidate_products(
            selected_item=selected_item,
            products=products,
            occasion=occasion,
            max_items=product_fetch_limit
        )

        if products:
            optional_product_groups.append(
                products[:min(
                    max_items_per_category,
                    MAX_OPTIONAL_PRODUCTS_PER_CATEGORY,
                )]
            )

    basic_outfits = build_basic_outfit_items(
        selected_item=selected_item,
        required_product_groups=required_product_groups
    )
    basic_outfits.sort(
        key=lambda outfit: calculate_compatibility_score(
            outfit_items=outfit,
            occasion=occasion,
        )["compatibility_score"],
        reverse=True,
    )
    basic_outfit_limit = min(
        MAX_BASIC_OUTFITS_TO_SCORE,
        max(10, max_outfits * 3),
    )
    basic_outfits = basic_outfits[:basic_outfit_limit]
    candidate_outfit_limit = min(
        MAX_CANDIDATE_OUTFITS_TO_SCORE,
        max(100, max_outfits * 25),
    )

    all_outfits = add_optional_items_to_outfits(
        basic_outfits=basic_outfits,
        optional_product_groups=optional_product_groups,
        max_candidates=candidate_outfit_limit,
    )
    all_outfits = deduplicate_outfit_items(all_outfits)

    scored_outfits = []

    for index, outfit_items in enumerate(all_outfits, start=1):
        score_result = calculate_hybrid_score(
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
            "rule_based_score": score_result["rule_based_score"],
            "ml_score": score_result["ml_score"],
            "ml_available": score_result["ml_available"],
            "reason_tags": score_result["reason_tags"],
            "score_breakdown": score_result["score_breakdown"],
            "applied_filters": {
                "min_price": min_price,
                "max_price": max_price,
                "preferred_colors": preferred_colors,
                "excluded_categories": excluded_categories,
                "max_items_per_category": max_items_per_category
            }
        }

        scored_outfits.append(outfit)

    ranked_outfits = sorted(
        scored_outfits,
        key=lambda outfit: outfit["compatibility_score"],
        reverse=True
    )
    ranked_outfits = diversify_ranked_outfits(
        ranked_outfits=ranked_outfits,
        selected_category=selected_category,
        selected_item_id=selected_item_id,
        max_outfits=max_outfits,
    )

    for rank, outfit in enumerate(ranked_outfits, start=1):
        outfit["outfit_id"] = f"OUT{rank:03d}"

    return {
        "success": True,
        "message": (
            "Outfits generated successfully. "
            f"No {', '.join(color_filter_mismatches)} products matched your selected "
            f"colors ({', '.join(preferred_colors or [])}) within the selected price range."
            if color_filter_mismatches
            else "Outfits generated successfully"
        ),
        "user_id": user_id,
        "selected_item_id": selected_item_id,
        "outfits": ranked_outfits
    }
