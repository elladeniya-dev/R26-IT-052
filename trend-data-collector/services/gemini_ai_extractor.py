"""
Autonomous AI Scraper for OutfitIQ using Google's Gemini Flash (Free API via modern google-genai SDK).
Provides self-healing e-commerce extraction that reads page meaning instead of brittle CSS tags or RegEx.
Immune to frontend design layout shifts and intelligently rejects base64 image placeholders and menu clutter.
"""
import os
import time
import json
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from dotenv import load_dotenv

from services.garment_validator import GarmentValidator

load_dotenv()

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logging.warning("modern google-genai SDK not installed. Gemini AI Scraper will be disabled.")


class GeminiAIExtractor:
    """
    Autonomous AI Scraper utilizing Gemini 2.5 Flash for structured e-commerce fashion extraction.
    """
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if modern SDK is installed and GEMINI_API_KEY is defined in environment."""
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        return GENAI_AVAILABLE and bool(api_key)

    @classmethod
    def extract_garments_from_page(
        cls,
        page_content: str,
        base_url: str,
        brand_name: str,
        segment: str,
        start_rank: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Send scraped webpage content (markdown/text/HTML snippet) to Gemini Flash to autonomously
        extract women's fashion garment data into structured JSON without custom CSS rules.
        """
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            logging.debug(f"[Gemini AI] GEMINI_API_KEY missing from environment/.env for {brand_name}. Skipping AI extraction.")
            return []
            
        try:
            client = genai.Client(api_key=api_key)
            
            # Trim content if excessive to keep latency lightning fast (around 60,000 chars is plenty for collection grids)
            clean_snippet = (page_content or "")[:60000]
            if len(clean_snippet) < 50:
                return []
                
            prompt = f"""
You are an advanced Autonomous AI E-Commerce Fashion Scraper for an academic trend research project in Sri Lanka.
Below is the content from a fashion retailer catalog page: Brand '{brand_name}', Base URL '{base_url}'.

Your instructions:
1. Analyze the semantic meaning of the text and links, ignoring CSS style variations or frontend layout complexities.
2. Extract authentic WOMEN'S fashion garment items suitable for the trendy 18-30 young female demographic (dresses, tops, casuals, co-ord sets, sarees, partywear, workwear). STRICTLY EXCLUDE and IGNORE any menswear, boys' attire, kids' clothing, baby products, or non-apparel homeware.
3. Completely ignore website navigation buttons, category banners (like 'New Arrivals', 'Clear All', 'Shop By Size', 'Next', 'Cart'), and promotional footers.
4. For each identified fashion item, provide exact details:
   - title: Exact descriptive name of the dress, outfit, or apparel item.
   - price_lkr: Numeric price in Sri Lankan Rupees (LKR/Rs). Convert formatted strings like "Rs. 4,990.00" or "4,990" directly into a float number (e.g. 4990.0). If the price is completely absent or 0, omit the item.
   - product_url: Absolute hyperlink URL pointing to the individual product page (must begin with http:// or https://, prepend '{base_url}' if relative).
   - primary_image_url: Real high-resolution JPG/PNG image URL of the garment. You MUST strictly reject any base64 transparent GIF placeholders ('data:image/gif;base64...').

Return a JSON object containing a single key "items" with an array of matching garment objects:
{{
  "items": [
    {{
      "title": "Floral Print Maxi Dress",
      "price_lkr": 5490.0,
      "product_url": "https://example.com/products/floral-dress-1",
      "primary_image_url": "https://cdn.example.com/images/floral-dress.jpg"
    }}
  ]
}}

Catalog Page Content:
{clean_snippet}
"""
            logging.info(f"   [Autonomous AI Scraper] Invoking Gemini Flash on {brand_name} catalog page...")
            
            models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash"]
            response = None
            for model_name in models_to_try:
                for attempt in range(2):
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                temperature=0.1,
                            )
                        )
                        break
                    except Exception as api_err:
                        err_str = str(api_err)
                        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                            if attempt == 0 and model_name == models_to_try[0]:
                                logging.warning(f"   [Gemini Quota Notice] Model {model_name} quota/rate limited on {brand_name}. Engaging fallback to gemini-1.5-flash...")
                                time.sleep(5.0)
                                break  # Break attempt loop to immediately attempt next fallback model
                            else:
                                backoff_sec = 15.0
                                logging.warning(f"   [Gemini AI Rate Limit on {model_name}] Pausing for {backoff_sec}s...")
                                time.sleep(backoff_sec)
                        else:
                            logging.warning(f"   [Gemini AI API Error on {model_name}]: {api_err}")
                            break
                if response and getattr(response, "text", None):
                    break

            if not response or not getattr(response, "text", None):
                return []
                
            # Polite inter-request throttling to preserve Free-Tier instantaneous quota (15 RPM)
            time.sleep(3.5)
            
            result_text = response.text
            data = json.loads(result_text)
            raw_items = data.get("items", []) if isinstance(data, dict) else []
            
            validated_garments = []
            rank = start_rank
            seen_urls = set()
            
            for item in raw_items:
                prod_url = item.get("product_url", "").strip()
                if not prod_url or prod_url in seen_urls:
                    continue
                if not prod_url.startswith("http"):
                    prod_url = urljoin(base_url, prod_url)
                seen_urls.add(prod_url)
                
                candidate = {
                    "rank_position": rank,
                    "title": item.get("title", "").strip(),
                    "product_url": prod_url,
                    "published_at": "",
                    "price_lkr": float(item.get("price_lkr", 0.0)),
                    "primary_image_url": item.get("primary_image_url", "").strip(),
                    "image_array": [item.get("primary_image_url", "").strip()] if item.get("primary_image_url") else [],
                    "shopify_tags": [],
                    "product_type": "apparel",
                    "source_name": brand_name,
                    "source_type": "tier3_autonomous_ai_gemini",
                    "market_segment": segment,
                }
                
                clean_item = GarmentValidator.validate_and_sanitize(candidate)
                if clean_item:
                    validated_garments.append(clean_item)
                    rank += 1
                    
            logging.info(f"   ---> [Gemini AI Success] Autonomously extracted and validated {len(validated_garments)} garments from {brand_name}.")
            return validated_garments

        except Exception as e:
            logging.warning(f"   [Gemini AI Extraction Error on {brand_name}]: {e}")
            return []
