import os
import json
from google import genai
from google.genai import types
from scripts.ml_taxonomy import HM_CATEGORIES, HM_PATTERNS, HM_COLORS
from pydantic import BaseModel, Field

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing. Please set it in your .env file.")

client = genai.Client(api_key=GEMINI_API_KEY)

class AttributeMappingResponse(BaseModel):
    mapped_category: str = Field(description="The closest category from the H&M taxonomy.")
    mapped_color: str = Field(description="The closest color from the H&M taxonomy.")
    mapped_pattern: str = Field(description="The closest pattern from the H&M taxonomy.")


def append_cdn_resize(url: str, width: int = 384) -> str:
    """Appends resizing parameters to known CDNs to dodge the Token Trap."""
    if not url: return url
    
    # Shopify CDN
    if "cdn.shopify.com" in url:
        if "?" in url: return f"{url}&width={width}"
        return f"{url}?width={width}"
        
    # GreenCloudPOS (used by Chenara Dodge, etc.)
    if "cdn.greencloudpos.com" in url:
        if "?" in url:
            # Replace existing width if present
            import re
            url = re.sub(r'width=\d+', f'width={width}', url)
            if 'width=' not in url:
                url += f"&width={width}"
            return url
        return f"{url}?width={width}"
        
    return url

def map_attributes_with_gemini(raw_title: str, raw_category: str, raw_color: str, raw_pattern: str, image_url: str):
    """
    Uses Gemini 3.7 Flash to map raw extracted attributes to the strict ML taxonomy.
    Passes the image URL directly to avoid downloading.
    """
    resized_url = append_cdn_resize(image_url)
    
    prompt = f"""
    You are an expert fashion taxonomist mapping messy real-world e-commerce data to a strict machine learning taxonomy.
    
    Product Title: {raw_title}
    Raw Extracted Category: {raw_category}
    Raw Extracted Color: {raw_color}
    Raw Extracted Pattern: {raw_pattern}
    
    Analyze the provided image and the raw text above. 
    Map the product to the STRICTEST closest match from these exact lists.
    
    Allowed Categories: {', '.join(HM_CATEGORIES)}
    Allowed Colors: {', '.join(HM_COLORS)}
    Allowed Patterns: {', '.join(HM_PATTERNS)}
    """
    
    contents = [prompt]
    
    if resized_url:
        # Pass the external URL directly per the new GenAI SDK
        contents.append(
            types.Part.from_uri(
                file_uri=resized_url,
                mime_type="image/jpeg" 
            )
        )
        
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AttributeMappingResponse,
                temperature=0.1 # Low temperature for strict taxonomy mapping
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        import logging
        logging.getLogger("OutfitIQ.GeminiMapper").error(f"Gemini Mapping Error for '{raw_title}': {e}")
        return None
