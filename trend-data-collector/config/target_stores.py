"""
Target Store Directory for OutfitIQ Trend Data Collector
Contains top Sri Lankan women's fashion e-commerce platforms categorized by market segment
and assigned to Hybrid Ingestion Tiers (Shopify Direct JSON vs Crawl4AI AI Extraction).
"""

TIER_1_SHOPIFY = "shopify_json_direct"
TIER_2_CRAWL4AI = "crawl4ai_headless_extraction"
LEGACY_HTML_FALLBACK = "legacy_html_scraping"

SEGMENT_HIGH_VELOCITY_BOUTIQUES = "High-Velocity Modern Boutiques"
SEGMENT_MASS_MARKET_DEPARTMENT = "Department Stores & Mass-Market Retailers"
SEGMENT_SPECIALTY_WORKWEAR = "Workwear, Premium & Specialty Designers"

SRI_LANKA_TARGET_STORES = [
    # --- 1. High-Velocity Modern Boutiques & Fast-Fashion ---
    {
        "brand_name": "GFlock",
        "domain": "gflock.lk",
        "base_url": "https://gflock.lk",
        "primary_style_focus": "Modern minimalism, linen, structured casuals",
        "segment": SEGMENT_HIGH_VELOCITY_BOUTIQUES,
        "ingestion_tier": TIER_1_SHOPIFY,
        "target_endpoints": [
            "/products.json?limit=250",
            "/collections/new-arrivals/products.json?limit=250",
        ],
    },
    {
        "brand_name": "Mimosa",
        "domain": "mimosaforever.com",
        "base_url": "https://mimosaforever.com",
        "primary_style_focus": "Elegant casuals, floral dresses, brunch wear",
        "segment": SEGMENT_HIGH_VELOCITY_BOUTIQUES,
        "ingestion_tier": TIER_1_SHOPIFY,
        "target_endpoints": [
            "/products.json?limit=250",
            "/collections/new-arrivals/products.json?limit=250",
        ],
    },
    {
        "brand_name": "Chenara Dodge",
        "domain": "chenaradodge.lk",
        "base_url": "https://chenaradodge.lk",
        "primary_style_focus": "Printed maxi/midi dresses, partywear",
        "segment": SEGMENT_HIGH_VELOCITY_BOUTIQUES,
        "ingestion_tier": TIER_1_SHOPIFY,
        "target_endpoints": ["/products.json?limit=250"],
    },
    {
        "brand_name": "Arienti",
        "domain": "arienti.lk",
        "base_url": "https://arienti.lk",
        "primary_style_focus": "Casual chic, linen edits, oversized basics",
        "segment": SEGMENT_HIGH_VELOCITY_BOUTIQUES,
        "ingestion_tier": TIER_1_SHOPIFY,
        "target_endpoints": ["/products.json?limit=250"],
    },
    {
        "brand_name": "Kelly Felder",
        "domain": "kellyfelder.com",
        "base_url": "https://kellyfelder.com",
        "primary_style_focus": "Trendy party frocks, evening wear, denim",
        "segment": SEGMENT_HIGH_VELOCITY_BOUTIQUES,
        "ingestion_tier": TIER_1_SHOPIFY,
        "target_endpoints": [
            "/products.json?limit=250",
            "/collections/new-arrivals/products.json?limit=250",
        ],
    },
    {
        "brand_name": "Nils Store",
        "domain": "nilsstore.com",
        "base_url": "https://nilsstore.com",
        "primary_style_focus": "Office casuals, everyday dresses, tunics",
        "segment": SEGMENT_HIGH_VELOCITY_BOUTIQUES,
        "ingestion_tier": TIER_1_SHOPIFY,
        "target_endpoints": ["/products.json?limit=250"],
    },
    {
        "brand_name": "Spring & Summer",
        "domain": "springandsummer.lk",
        "base_url": "https://www.springandsummer.lk",
        "primary_style_focus": "Feminine dresses, seasonal collections",
        "segment": SEGMENT_HIGH_VELOCITY_BOUTIQUES,
        "ingestion_tier": TIER_2_CRAWL4AI,
        "target_endpoints": ["/collections/women", "/new-arrivals"],
    },
    {
        "brand_name": "ZigZag",
        "domain": "zigzag.lk",
        "base_url": "https://zigzag.lk",
        "primary_style_focus": "Bold prints, casual dresses, youth fashion",
        "segment": SEGMENT_HIGH_VELOCITY_BOUTIQUES,
        "ingestion_tier": TIER_1_SHOPIFY,
        "target_endpoints": [
            "/products.json?limit=250",
            "/collections/new-arrivals-1/products.json?limit=250",
        ],
    },
    {
        "brand_name": "JoeY Clothing",
        "domain": "joeyclothing.com",
        "base_url": "https://joeyclothing.com",
        "primary_style_focus": "Ribbed tops, twisted tees, linen sets",
        "segment": SEGMENT_HIGH_VELOCITY_BOUTIQUES,
        "ingestion_tier": TIER_1_SHOPIFY,
        "target_endpoints": ["/products.json?limit=250"],
    },
    {
        "brand_name": "Lurreli",
        "domain": "lurreli.lk",
        "base_url": "https://lurreli.lk",
        "primary_style_focus": "Evening wear, denim, workwear edits",
        "segment": SEGMENT_HIGH_VELOCITY_BOUTIQUES,
        "ingestion_tier": TIER_1_SHOPIFY,
        "target_endpoints": ["/products.json?limit=250"],
    },
    {
        "brand_name": "Bellini",
        "domain": "bellini.lk",
        "base_url": "https://bellini.lk",
        "primary_style_focus": "Affordable crop tops, everyday casuals",
        "segment": SEGMENT_HIGH_VELOCITY_BOUTIQUES,
        "ingestion_tier": TIER_1_SHOPIFY,
        "target_endpoints": ["/products.json?limit=250"],
    },
    {
        "brand_name": "Flamingo SL",
        "domain": "flamingosl.com",
        "base_url": "https://flamingosl.com",
        "primary_style_focus": "Party dresses, statement evening wear",
        "segment": SEGMENT_HIGH_VELOCITY_BOUTIQUES,
        "ingestion_tier": TIER_1_SHOPIFY,
        "target_endpoints": ["/products.json?limit=250"],
    },
    {
        "brand_name": "Jezza Fashion",
        "domain": "jezzafashions.com",
        "base_url": "https://jezzafashions.com",
        "primary_style_focus": "A-line dresses, crepe satin, office tops",
        "segment": SEGMENT_HIGH_VELOCITY_BOUTIQUES,
        "ingestion_tier": TIER_1_SHOPIFY,
        "target_endpoints": ["/products.json?limit=250"],
    },
    # --- 2. Department Stores & Mass-Market Retailers ---
    {
        "brand_name": "Odel",
        "domain": "odel.lk",
        "base_url": "https://odel.lk",
        "primary_style_focus": "Multi-brand luxury & street casuals",
        "segment": SEGMENT_MASS_MARKET_DEPARTMENT,
        "ingestion_tier": TIER_2_CRAWL4AI,
        "target_endpoints": ["/women", "/women/new-arrivals"],
    },
    {
        "brand_name": "Cool Planet",
        "domain": "coolplanet.lk",
        "base_url": "https://coolplanet.lk",
        "primary_style_focus": "Mass-market apparel, denim, casuals",
        "segment": SEGMENT_MASS_MARKET_DEPARTMENT,
        "ingestion_tier": TIER_2_CRAWL4AI,
        "target_endpoints": ["/collections/women"],
    },
    {
        "brand_name": "Nolimit",
        "domain": "nolimit.lk",
        "base_url": "https://www.nolimit.lk",
        "primary_style_focus": "Affordable everyday wear, ethnic & western",
        "segment": SEGMENT_MASS_MARKET_DEPARTMENT,
        "ingestion_tier": TIER_2_CRAWL4AI,
        "target_endpoints": ["/women", "/new-arrivals"],
    },
    {
        "brand_name": "Glitz",
        "domain": "glitz.lk",
        "base_url": "https://glitz.lk",
        "primary_style_focus": "Affordable everyday wear, lifestyle apparel",
        "segment": SEGMENT_MASS_MARKET_DEPARTMENT,
        "ingestion_tier": TIER_2_CRAWL4AI,
        "target_endpoints": ["/women"],
    },
    {
        "brand_name": "Fashion Bug",
        "domain": "fashionbug.lk",
        "base_url": "https://fashionbug.lk",
        "primary_style_focus": "Casuals, office wear, traditional wear",
        "segment": SEGMENT_MASS_MARKET_DEPARTMENT,
        "ingestion_tier": TIER_2_CRAWL4AI,
        "target_endpoints": ["/product-category/women/"],
    },
    {
        "brand_name": "House of Fashions",
        "domain": "houseoffashions.lk",
        "base_url": "https://www.houseoffashions.lk",
        "primary_style_focus": "Broad multi-category apparel",
        "segment": SEGMENT_MASS_MARKET_DEPARTMENT,
        "ingestion_tier": TIER_2_CRAWL4AI,
        "target_endpoints": ["/category/women"],
    },
    {
        "brand_name": "Kandy Selection",
        "domain": "kandyselection.lk",
        "base_url": "https://kandyselection.lk",
        "primary_style_focus": "Everyday casuals, dresses, workwear",
        "segment": SEGMENT_MASS_MARKET_DEPARTMENT,
        "ingestion_tier": TIER_2_CRAWL4AI,
        "target_endpoints": ["/product-category/women/"],
    },
    {
        "brand_name": "TFC (The Factory Outlet)",
        "domain": "tfcostore.com",
        "base_url": "https://tfcostore.com",
        "primary_style_focus": "Discounted fashion, casual basics",
        "segment": SEGMENT_MASS_MARKET_DEPARTMENT,
        "ingestion_tier": TIER_2_CRAWL4AI,
        "target_endpoints": ["/women"],
    },
    # --- 3. Workwear, Premium & Specialty Designers ---
    {
        "brand_name": "Mondy",
        "domain": "mondy.lk",
        "base_url": "https://www.mondy.lk",
        "primary_style_focus": "Power dressing, formal trousers, blazers",
        "segment": SEGMENT_SPECIALTY_WORKWEAR,
        "ingestion_tier": TIER_2_CRAWL4AI,
        "target_endpoints": ["/work-wear", "/dresses"],
    },
    {
        "brand_name": "Avirate",
        "domain": "aviratefashion.com",
        "base_url": "https://aviratefashion.com",
        "primary_style_focus": "Premium evening gowns, cocktail dresses",
        "segment": SEGMENT_SPECIALTY_WORKWEAR,
        "ingestion_tier": TIER_2_CRAWL4AI,
        "target_endpoints": ["/collections/dresses", "/collections/evening-wear"],
    },
    {
        "brand_name": "Cotton Collection",
        "domain": "cottoncollection.lk",
        "base_url": "https://cottoncollection.lk",
        "primary_style_focus": "Pure cotton, boho-chic, relaxed lounge",
        "segment": SEGMENT_SPECIALTY_WORKWEAR,
        "ingestion_tier": TIER_2_CRAWL4AI,
        "target_endpoints": ["/women"],
    },
    {
        "brand_name": "Lovi Ceylon",
        "domain": "loviceylon.com",
        "base_url": "https://loviceylon.com",
        "primary_style_focus": "Modern Sri Lankan heritage & luxury sarongs",
        "segment": SEGMENT_SPECIALTY_WORKWEAR,
        "ingestion_tier": TIER_1_SHOPIFY,
        "target_endpoints": ["/products.json?limit=250"],
    },
    {
        "brand_name": "KYRA",
        "domain": "kyraloves.com",
        "base_url": "https://kyraloves.com",
        "primary_style_focus": "Trendy casual tops, youthful dresses",
        "segment": SEGMENT_SPECIALTY_WORKWEAR,
        "ingestion_tier": TIER_1_SHOPIFY,
        "target_endpoints": ["/products.json?limit=250"],
    },
    {
        "brand_name": "Amante",
        "domain": "amante.lk",
        "base_url": "https://amante.lk",
        "primary_style_focus": "Loungewear, activewear, intimates",
        "segment": SEGMENT_SPECIALTY_WORKWEAR,
        "ingestion_tier": TIER_1_SHOPIFY,
        "target_endpoints": ["/products.json?limit=250"],
    },
]


def get_stores_by_tier(tier: str) -> list[dict]:
    """Return all configured target stores matching a specific ingestion tier."""
    return [
        store
        for store in SRI_LANKA_TARGET_STORES
        if store.get("ingestion_tier") == tier
    ]


def get_stores_by_segment(segment: str) -> list[dict]:
    """Return all target stores in a specific market segment."""
    return [
        store for store in SRI_LANKA_TARGET_STORES if store.get("segment") == segment
    ]
