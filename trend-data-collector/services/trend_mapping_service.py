from datetime import datetime, timezone
from collections import defaultdict

KEYWORD_MAP = {
    "style": [
        "oversized",
        "casual",
        "formal",
        "streetwear",
        "minimal",
        "minimalist",
        "vintage",
        "retro",
        "old money",
        "party",
        "office",
        "basic",
        "essential",
        "classic",
        "sculpt",
        "sculpted",
        "soft",
        "modern",
        "urban",
        "botanist",
        "gallery",
        "studio",
        "pastel",
        "summer",
        "bloom",
        "wrap",
        "bias",
        "polo",
        "peplum",
        "bustier",
        "cowl neck",
        "halter neck",
        "off shoulder",
    ],
    "material": [
        "linen",
        "cotton",
        "denim",
        "non denim",
        "leather",
        "silk",
        "satin",
        "ribbed",
        "knit",
        "mesh",
        "chiffon",
        "twill",
        "lace",
        "woven",
    ],
    "color": [
        "black",
        "white",
        "off-white",
        "beige",
        "brown",
        "red",
        "blue",
        "navy",
        "green",
        "pink",
        "cream",
        "grey",
        "gray",
        "yellow",
        "purple",
        "orange",
        "sand",
        "maroon",
        "burgundy",
        "pastel",
    ],
    "fit_type": [
        "baggy",
        "slim",
        "slim fit",
        "relaxed",
        "regular",
        "cropped",
        "crop",
        "loose",
        "skinny",
        "wide leg",
        "straight leg",
        "high waist",
        "mid waist",
        "bodycon",
        "fitted",
        "flare",
        "flared",
        "sleeveless",
        "short sleeve",
        "long sleeve",
        "half sleeve",
        "puff sleeve",
        "balloon sleeve",
        "cap sleeve",
    ],
    "pattern": [
        "floral",
        "stripe",
        "striped",
        "check",
        "checked",
        "solid",
        "graphic",
        "printed",
        "print",
        "polka",
        "polka dotted",
        "block print",
        "block printed",
        "animal print",
        "line art",
    ],
    "category": [
        "dress",
        "dresses",
        "mini dress",
        "maxi dress",
        "midi dress",
        "column dress",
        "polo dress",
        "wrap dress",
        "top",
        "tops",
        "crop top",
        "bra top",
        "bralette",
        "shirt",
        "shirts",
        "tshirt",
        "t-shirt",
        "tee",
        "blouse",
        "jeans",
        "pants",
        "pant",
        "trouser",
        "trousers",
        "skirt",
        "mini skirt",
        "maxi skirt",
        "midi skirt",
        "short",
        "shorts",
        "jacket",
        "hoodie",
        "cardigan",
        "blazer",
        "jumpsuit",
        "flight suit",
        "bodysuit",
        "kurtha",
        "kaftan",
    ],
}


def normalize_attribute_value(attribute_type: str, keyword: str) -> str:
    value = keyword.strip().lower()

    replacements = {
        "t-shirt": "tshirt",
        "tee": "tshirt",
        "shirts": "shirt",
        "tops": "top",
        "dresses": "dress",
        "trousers": "trouser",
        "pants": "pant",
        "shorts": "short",
        "gray": "grey",
        "minimal": "minimalist",
        "printed": "print",
        "block printed": "block print",
        "striped": "stripe",
        "checked": "check",
        "polka": "polka dot",
        "polka dotted": "polka dot",
        "non denim": "non-denim",
        "crop": "cropped",
        "flared": "flare",
    }

    return replacements.get(value, value)


def map_products_to_trend_observations(
    products: list[dict], source_name: str, source_type: str
) -> list[dict]:
    grouped_signals = defaultdict(
        lambda: {
            "mention_count": 0,
            "rank_positions": [],
            "keywords": set(),
            "segments": set(),
        }
    )

    for product in products:
        title = product.get("title", "")
        rank_position = product.get("rank_position")
        shopify_tags = " ".join(product.get("shopify_tags", []))
        product_type = product.get("product_type", "")
        market_segment = product.get("market_segment", "General")

        searchable_text = (
            f" {title.lower()} {product_type.lower()} {shopify_tags.lower()} "
        )

        for attribute_type, keywords in KEYWORD_MAP.items():
            for keyword in keywords:
                keyword_lower = keyword.lower()
                keyword_pattern = f" {keyword_lower} "

                if keyword_pattern in searchable_text:
                    attribute_value = normalize_attribute_value(
                        attribute_type=attribute_type, keyword=keyword_lower
                    )

                    key = (attribute_type, attribute_value)

                    grouped_signals[key]["mention_count"] += 1

                    if rank_position is not None:
                        grouped_signals[key]["rank_positions"].append(rank_position)

                    grouped_signals[key]["keywords"].add(keyword_lower)
                    grouped_signals[key]["segments"].add(market_segment)

    observations = []
    collected_at = datetime.now(timezone.utc).isoformat()

    for (attribute_type, attribute_value), data in grouped_signals.items():
        rank_positions = data["rank_positions"]

        if rank_positions:
            average_rank = round(sum(rank_positions) / len(rank_positions))
        else:
            average_rank = None

        segments_str = ", ".join(sorted(data["segments"]))

        observations.append(
            {
                "source_name": source_name,
                "source_type": source_type,
                "attribute_type": attribute_type,
                "attribute_value": attribute_value,
                "keyword": ", ".join(sorted(data["keywords"])),
                "mention_count": data["mention_count"],
                "rank_position": average_rank,
                "collected_at": collected_at,
                "market_segment": segments_str,
            }
        )

    observations.sort(key=lambda item: item["mention_count"], reverse=True)

    return observations
