import json
import re
from pathlib import Path

file_path = Path("output") / "combined_srilanka_raw_garments.json"
if not file_path.exists():
    print("File not found:", file_path)
    exit(1)

data = json.loads(file_path.read_text("utf-8"))
total = len(data)

print("================ OUTFITIQ DATA QUALITY FORENSIC AUDIT ================")
print(f"Total Garments Harvested: {total}")

# 1. Defective Prices (< 500 LKR or > 500,000 LKR)
zero_or_bad_prices = [d for d in data if d.get("price_lkr", 0.0) < 500.0 or d.get("price_lkr", 0.0) > 500000.0]
print(f"1. Defective / Zero Prices:            {len(zero_or_bad_prices)} ({100 * len(zero_or_bad_prices) / max(1, total):.2f}%)")

# 2. Base64 Dummy Image Placeholders
base64_imgs = [d for d in data if "data:image" in str(d.get("primary_image_url", ""))]
print(f"2. Base64 Dummy Image Placeholders:    {len(base64_imgs)} ({100 * len(base64_imgs) / max(1, total):.2f}%)")

# 3. Demographic Leakage (Menswear, Kids, Baby)
leak_regex = re.compile(r"\b(mens?|gents?|males?|boys?|kids?|bab(y|ies)|toddlers?|children|maternity)\b", re.IGNORECASE)
leaked = [d for d in data if leak_regex.search(str(d.get("title", "")))]
print(f"3. Menswear / Kids Demographic Leak:   {len(leaked)} ({100 * len(leaked) / max(1, total):.2f}%)")

# 4. Price Telemetry
prices = [d["price_lkr"] for d in data if isinstance(d.get("price_lkr"), (int, float))]
if prices:
    print("\n--- Price Telemetry & Market Realism ---")
    print(f"Minimum Price: {min(prices):,.2f} LKR")
    print(f"Maximum Price: {max(prices):,.2f} LKR")
    print(f"Average Price: {sum(prices) / len(prices):,.2f} LKR")

# 5. Store breakdown & samples
print("\n--- Verified Young Women's Fashion Sample Excerpts ---")
sample_indices = [0, len(data)//4, len(data)//2, (3*len(data))//4, len(data)-1] if total >= 5 else range(total)
for idx in sample_indices:
    item = data[idx]
    title = str(item.get("title", ""))[:38]
    price = float(item.get("price_lkr", 0.0))
    source = str(item.get("source_name", ""))
    seg = str(item.get("market_segment", ""))
    print(f" * [{source:<14}] {title:<40} | {price:>10,.2f} LKR | {seg}")

print("======================================================================")
