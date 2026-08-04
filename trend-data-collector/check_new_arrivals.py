import json
from pathlib import Path

file_path = Path("output") / "combined_srilanka_raw_garments.json"
if not file_path.exists():
    print("File not found:", file_path)
    exit(1)

data = json.loads(file_path.read_text("utf-8"))
total = len(data)

# Detect New Arrivals via URL path routing, Shopify tag labels, or product titles
new_arrivals = []
for d in data:
    url = str(d.get("product_url", "")).lower()
    tags = [str(t).lower() for t in d.get("shopify_tags", [])]
    title = str(d.get("title", "")).lower()
    
    is_new = (
        "new-arrival" in url or
        "/new/" in url or
        any("new" in t or "latest" in t or "2026" in t or "drop" in t for t in tags) or
        "new arrival" in title
    )
    if is_new:
        new_arrivals.append(d)

print("================ NEW ARRIVALS & RECENT DROPS AUDIT ================")
print(f"Total Garments Analyzed: {total}")
print(f"Identified New Arrivals: {len(new_arrivals)} ({100 * len(new_arrivals) / max(1, total):.2f}% of total catalog)")

by_brand = {}
for d in new_arrivals:
    brand = d.get("source_name", "Unknown")
    by_brand[brand] = by_brand.get(brand, 0) + 1

print("\n--- New Arrivals Count by Retail Brand ---")
for brand, count in sorted(by_brand.items(), key=lambda x: x[1], reverse=True):
    print(f" * {brand:<20}: {count:>3} garments ({100*count/len(new_arrivals):.1f}% of new drops)")

print("\n--- Sample Identified New Arrival Garments ---")
for item in new_arrivals[:8]:
    source = str(item.get("source_name", ""))
    title = str(item.get("title", ""))[:38]
    price = float(item.get("price_lkr", 0.0))
    tags_str = ", ".join(item.get("shopify_tags", [])[:3])
    print(f" * [{source:<14}] {title:<40} | {price:>8,.2f} LKR | Tags: [{tags_str}]")

print("===================================================================")
