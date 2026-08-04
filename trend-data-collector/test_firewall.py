from services.garment_validator import GarmentValidator

samples = [
    {
        "title": "Floral Linen Brunch Co-Ord Set",
        "product_url": "https://gflock.lk/products/floral-set",
        "price_lkr": "Rs. 7,490.00",
        "primary_image_url": "https://cdn.example.com/a.jpg",
        "shopify_tags": ["women", "dress", "linen"]
    },
    {
        "title": "Men's Regular Polo Shirt - Navy",
        "product_url": "https://odel.lk/men/polo-1",
        "price_lkr": 3500.0,
        "primary_image_url": "https://cdn.example.com/b.jpg",
        "shopify_tags": ["men", "polo"]
    },
    {
        "title": "Gents Formal Office Trouser",
        "product_url": "https://nolimit.lk/gents/trouser",
        "price_lkr": 4200.0,
        "primary_image_url": "https://cdn.example.com/c.jpg"
    },
    {
        "title": "Baby Cotton Romper 3-6M",
        "product_url": "https://coolplanet.lk/baby/romper",
        "price_lkr": 1500.0,
        "primary_image_url": "https://cdn.example.com/d.jpg"
    },
    {
        "title": "Satin Midi Evening Slip Dress",
        "product_url": "https://mimosaforever.com/products/slip-dress",
        "price_lkr": 11900.0,
        "primary_image_url": "https://cdn.example.com/e.jpg"
    }
]

print("\n================ DEMOGRAPHIC FIREWALL VERIFICATION ================")
for s in samples:
    res = GarmentValidator.validate_and_sanitize(s)
    status = "[ACCEPTED - YOUNG FEMALE TARGET]" if res else "[REJECTED - DEMOGRAPHIC EXCLUSION]"
    print(f"Item: {s['title']:<32} | URL Path: {s['product_url'][:30]:<30} -> {status}")
print("====================================================================\n")
