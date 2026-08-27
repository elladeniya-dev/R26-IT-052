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
        # FIXED: base_url was chenaradodge.com — that domain only routes email.
        # Live storefront (new-arrivals, products, vouchers) is on the .lk domain.
        "domain": "chenaradodge.lk",
        "base_url": "https://chenaradodge.lk",
        "primary_style_focus": "Printed maxi/midi dresses, partywear",
        "segment": SEGMENT_HIGH_VELOCITY_BOUTIQUES,
        "ingestion_tier": TIER_2_CRAWL4AI,
        "target_endpoints": ["/new-arrivals", "/dresses", "/shop"],
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
        # FIXED: was tagged Tier 1 Shopify, but the live site uses /dresses and
        # /best-sellers/... paths with no /collections/ structure — not Shopify.
        "domain": "nilsonline.lk",
        "base_url": "https://www.nilsonline.lk",
        "primary_style_focus": "Office casuals, everyday dresses, tunics",
        "segment": SEGMENT_HIGH_VELOCITY_BOUTIQUES,
        "ingestion_tier": TIER_2_CRAWL4AI,
        "target_endpoints": ["/dresses", "/best-sellers"],
    },
    {
        "brand_name": "Spring & Summer",
        # FIXED: was tagged Tier 2, but the live site is Shopify (/collections/,
        # /pages/about-us) — /products.json will work directly.
        "domain": "springandsummer.lk",
        "base_url": "https://www.springandsummer.lk",
        "primary_style_focus": "Feminine dresses, seasonal collections",
        "segment": SEGMENT_HIGH_VELOCITY_BOUTIQUES,
        "ingestion_tier": TIER_1_SHOPIFY,
        "target_endpoints": ["/products.json?limit=250"],
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
        "ingestion_tier": TIER_2_CRAWL4AI,
        "target_endpoints": ["/shop", "/women", "/collections/all"],
    },
    {
        "brand_name": "Jezza Fashion",
        # Note: also seen as jezzafashion.com (no "s") on their Facebook page —
        # jezzafashions.com is the confirmed working storefront.
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
        "ingestion_tier": TIER_1_SHOPIFY,
        "target_endpoints": ["/products.json?limit=250"],
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
        # FLAG (not fixed): a 2023 company post says "Glitz Evolves into NOLIMIT."
        # If that merger is complete, this may now duplicate Nolimit's catalog —
        # spot-check both before spending scraper budget on Glitz.
        "domain": "glitz.lk",
        "base_url": "https://glitz.lk",
        "primary_style_focus": "Affordable everyday wear, lifestyle apparel",
        "segment": SEGMENT_MASS_MARKET_DEPARTMENT,
        "ingestion_tier": TIER_2_CRAWL4AI,
        "target_endpoints": ["/product-category/women"],
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
        # FIXED: was tagged Tier 2, but the live site is Shopify
        # (/collections/, /products/) — /products.json will work directly.
        "domain": "houseoffashions.lk",
        "base_url": "https://houseoffashions.lk",
        "primary_style_focus": "Broad multi-category apparel",
        "segment": SEGMENT_MASS_MARKET_DEPARTMENT,
        "ingestion_tier": TIER_1_SHOPIFY,
        "target_endpoints": ["/products.json?limit=250"],
    },
    {
        "brand_name": "Kandy Selection",
        "domain": "kandyselection.lk",
        "base_url": "https://kandyselection.lk",
        "primary_style_focus": "Everyday casuals, dresses, workwear",
        "segment": SEGMENT_MASS_MARKET_DEPARTMENT,
        "ingestion_tier": TIER_2_CRAWL4AI,
        "target_endpoints": ["/shop/category/women"],
    },
    # [Offline/DNS Unresolved in 2026 — reconfirmed]
    # {
    #     "brand_name": "TFC (The Factory Outlet)",
    #     "domain": "tfcostore.com",
    #     "base_url": "https://tfcostore.com",
    #     "primary_style_focus": "Discounted fashion, casual basics",
    #     "segment": SEGMENT_MASS_MARKET_DEPARTMENT,
    #     "ingestion_tier": TIER_2_CRAWL4AI,
    #     "target_endpoints": ["/women"],
    # },
    # --- 3. Workwear, Premium & Specialty Designers ---
    # [Offline/DNS Unresolved in 2026]
    # {
    #     "brand_name": "Mondy",
    #     "domain": "mondy.lk",
    #     "base_url": "https://www.mondy.lk",
    #     "primary_style_focus": "Power dressing, formal trousers, blazers",
    #     "segment": SEGMENT_SPECIALTY_WORKWEAR,
    #     "ingestion_tier": TIER_2_CRAWL4AI,
    #     "target_endpoints": ["/work-wear", "/dresses"],
    # },
    {
        "brand_name": "Avirate",
        "domain": "aviratefashion.com",
        "base_url": "https://aviratefashion.com",
        "primary_style_focus": "Premium evening gowns, cocktail dresses",
        "segment": SEGMENT_SPECIALTY_WORKWEAR,
        "ingestion_tier": TIER_2_CRAWL4AI,
        "target_endpoints": ["/collections/dresses", "/collections/evening-wear"],
    },
    # [Not a dead domain — brand was acquired, not shuttered]
    # Cotton Collection was acquired by ODEL/Softlogic; the standalone domain
    # is gone but the brand's current inventory is browsable inside ODEL:
    # https://odel.lk/cotton-collection/br/1610 — pull it via the Odel
    # ingestion path with a brand filter instead of a standalone scraper.
    {
        "brand_name": "Lovi Ceylon",
        # FIXED: loviceylon.com does not resolve to the working storefront —
        # the live site is lovisarongs.com. Also note: this brand is sarongs /
        # national dress / luxury formalwear ($100-450 price range), not
        # everyday trend fashion — keep as a low-weight/optional source unless
        # you specifically want a premium-formalwear signal.
        "domain": "lovisarongs.com",
        "base_url": "https://lovisarongs.com",
        "primary_style_focus": "Modern Sri Lankan heritage & luxury sarongs",
        "segment": SEGMENT_SPECIALTY_WORKWEAR,
        "ingestion_tier": TIER_1_SHOPIFY,
        "target_endpoints": ["/products.json?limit=250"],
    },
    # [Offline/DNS Unresolved in 2026]
    # {
    #     "brand_name": "KYRA",
    #     "domain": "kyraloves.com",
    #     "base_url": "https://kyraloves.com",
    #     "primary_style_focus": "Trendy casual tops, youthful dresses",
    #     "segment": SEGMENT_SPECIALTY_WORKWEAR,
    #     "ingestion_tier": TIER_1_SHOPIFY,
    #     "target_endpoints": ["/products.json?limit=250"],
    # },
]
