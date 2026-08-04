"""
Enterprise Data Validation and Sanitization Firewall for OutfitIQ.
Ensures zero tainted data, incomplete product entries, base64 image placeholders,
or navigation menu text pollute the PostgreSQL store or downstream ML pipelines.
"""
import re
import logging

logger = logging.getLogger("OutfitIQ.Validator")

# Blacklisted titles resulting from menu scraping or navigation clutter
BLACKLISTED_TITLES = {
    "new arrivals", "clear all", "next", "shop by size", "loading",
    "home", "cart", "quick view", "sale", "menu", "view all",
    "women", "collection", "filter", "sort by", "page", "previous",
    "add to cart", "buy now", "search", "out of stock", "login"
}

# Regex pattern for isolating numeric currency figures in strings (e.g. "Rs. 12,490.00")
PRICE_REGEX = re.compile(r"(\d+(?:,\d+)*(?:\.\d{1,2})?)")

# Demographic exclusion regex: strictly reject menswear, children's clothing, and baby items
# Utilizes word boundaries (\b) to avoid false matches on terms like "women" or "garment"
EXCLUDED_DEMOGRAPHIC_REGEX = re.compile(
    r"\b(mens?|gent(s|lemen)?|males?|boys?|kids?|bab(y|ies)|toddlers?|children|maternity|newborn|infants?)\b",
    re.IGNORECASE
)
EXCLUDED_URL_PATHS = {"/men/", "/mens/", "/gents/", "/male/", "/kids/", "/boys/", "/baby/", "/children/", "/maternity/"}


class GarmentValidator:
    """
    Data hygiene and security firewall for raw e-commerce garment extraction.
    """
    
    @classmethod
    def validate_and_sanitize(cls, item: dict) -> dict:
        """
        Inspect and scrub a candidate item dictionary against production requirements.
        Returns a sanitized dictionary if valid, or empty dictionary `{}` if defective.
        """
        if not isinstance(item, dict):
            return {}
            
        # 1. Validate Product Title & Demographic Target (Women 18-30 focus, excluding menswear/kids)
        raw_title = str(item.get("title", "")).strip()
        if len(raw_title) < 3 or len(raw_title) > 200:
            return {}
        if raw_title.lower() in BLACKLISTED_TITLES or re.match(r"^\d+$", raw_title):
            return {}
        if EXCLUDED_DEMOGRAPHIC_REGEX.search(raw_title):
            return {}

        # 2. Sanitize and Verify Product URL (Excluding menswear/kids navigation paths)
        raw_url = str(item.get("product_url", "")).strip()
        if not raw_url or not raw_url.startswith("http"):
            return {}
        if "javascript:" in raw_url.lower() or "data:" in raw_url.lower():
            return {}
        url_lower_path = raw_url.lower()
        if any(bad_path in url_lower_path for bad_path in EXCLUDED_URL_PATHS):
            return {}
        # Also check tags if available
        tags = [str(t).lower().strip() for t in item.get("shopify_tags", []) if isinstance(t, str)]
        if any(EXCLUDED_DEMOGRAPHIC_REGEX.search(tag) for tag in tags):
            return {}

        # 3. Price Sanitization and Normalization (> 0 LKR required)
        raw_price = item.get("price_lkr", 0.0)
        clean_price = 0.0
        try:
            if isinstance(raw_price, (int, float)):
                clean_price = float(raw_price)
            elif isinstance(raw_price, str):
                match = PRICE_REGEX.search(raw_price)
                if match:
                    clean_price = float(match.group(1).replace(",", ""))
        except (ValueError, TypeError):
            clean_price = 0.0
            
        # Ignore items outside normal fashion pricing thresholds (e.g., test items or errors)
        if clean_price < 500.0 or clean_price > 500000.0:
            return {}

        # 4. Image Hygiene: reject base64 GIF placeholders and enforce CDN links
        primary_img = str(item.get("primary_image_url", "")).strip()
        if "data:image" in primary_img or not primary_img.startswith("http"):
            # Attempt fallback recovery from image array if primary link is broken/placeholder
            image_array = item.get("image_array", [])
            valid_img = next(
                (str(img).strip() for img in image_array if isinstance(img, str) and img.strip().startswith("http") and "data:image" not in img),
                None
            )
            if not valid_img:
                return {}
            primary_img = valid_img

        # 5. Assemble final normalized schema
        return {
            "rank_position": int(item.get("rank_position", 1)),
            "title": raw_title,
            "product_url": raw_url,
            "published_at": str(item.get("published_at", "")).strip(),
            "price_lkr": round(clean_price, 2),
            "primary_image_url": primary_img,
            "image_array": [str(x) for x in item.get("image_array", []) if isinstance(x, str) and x.startswith("http")],
            "shopify_tags": [str(t).lower().strip() for t in item.get("shopify_tags", []) if isinstance(t, str)],
            "product_type": str(item.get("product_type", "apparel")).strip() or "apparel",
            "source_name": str(item.get("source_name", "Unknown")).strip(),
            "source_type": str(item.get("source_type", "unknown")).strip(),
            "market_segment": str(item.get("market_segment", "General")).strip()
        }
