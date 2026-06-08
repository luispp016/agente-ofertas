import os
import requests
import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

def check_rules_filter(title, query, exclude_words, min_price_cop, max_price_cop, price_cop):
    """
    Applies rule-based filters: exclusion keywords, price thresholds, and simple text matching.
    """
    # 1. Check price boundaries
    if price_cop < min_price_cop or price_cop > max_price_cop:
        logger.debug(f"Filtered out by price ({price_cop} COP): {title}")
        return False
        
    title_lower = title.lower()
    query_words = [w.lower() for w in query.split() if len(w) > 2]
    
    # 2. Check exclusion keywords
    for word in exclude_words:
        # Match word boundaries to prevent false positives (e.g. matching "caja" in "cajamarca")
        pattern = rf"\b{word.lower()}\b"
        import re
        if re.search(pattern, title_lower):
            logger.debug(f"Filtered out by exclusion word '{word}': {title}")
            return False
            
    # 3. Check that the title is sufficiently related to the query
    # E.g., at least some of the search query words must be present in the title
    match_count = sum(1 for qw in query_words if qw in title_lower)
    if len(query_words) > 0 and match_count == 0:
        logger.debug(f"Filtered out due to 0 query word overlap: {title}")
        return False
        
    return True

def check_gemini_filter(title, target_product):
    """
    Uses the Gemini API to verify if the scraped title matches the target product.
    Returns True if it is a match, False otherwise.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return True # Fallback: assume matches if no API key is set
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = (
        f"Determine if the product title '{title}' refers to the actual product '{target_product}' "
        "or if it is an accessory, replacement part, digital item, subscription, protection plan, or box only. "
        "For example, if the target is 'Nintendo Switch OLED', a case or charger is NOT a match.\n"
        "Respond ONLY with 'MATCH' or 'NO_MATCH'."
    )
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 5
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            res_data = response.json()
            # Extract content from response structure
            candidates = res_data.get("candidates", [])
            if candidates:
                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                if "NO_MATCH" in text:
                    logger.info(f"Gemini API filtered out: '{title}' for target '{target_product}'")
                    return False
                elif "MATCH" in text:
                    logger.debug(f"Gemini API matched: '{title}'")
                    return True
        else:
            logger.warning(f"Gemini API returned status code {response.status_code}. Skipping AI filter.")
    except Exception as e:
        logger.error(f"Error querying Gemini API: {e}")
        
    return True # fallback to True on error to not lose deals

def process_and_compare_deals(all_scraped_items, product_config, rates):
    """
    Processes all scraped items, applies rules and optional AI filtering, 
    and returns a sorted list of matched items.
    """
    from .currency import convert_to_cop
    
    name = product_config["name"]
    exclude_words = product_config.get("exclude_words", [])
    min_price_cop = product_config.get("min_price_cop", 0)
    max_price_cop = product_config.get("max_price_cop", 999999999)
    
    processed_items = []
    
    for item in all_scraped_items:
        # Convert price to COP
        price_cop = convert_to_cop(item["price"], item["currency"], rates)
        item["price_cop"] = price_cop
        
        # 1. Apply Rule-based filters
        if not check_rules_filter(item["title"], name, exclude_words, min_price_cop, max_price_cop, price_cop):
            continue
            
        processed_items.append(item)
        
    # 2. Apply AI Filter if enabled in env/config (only for remaining items to save API calls)
    gemini_enabled = os.environ.get("GEMINI_API_KEY") is not None
    if gemini_enabled:
        logger.info(f"Applying Gemini AI filtering for {len(processed_items)} items of '{name}'...")
        filtered_items = []
        for item in processed_items:
            if check_gemini_filter(item["title"], name):
                filtered_items.append(item)
        processed_items = filtered_items
        
    # Sort items by price (ascending)
    processed_items.sort(key=lambda x: x["price_cop"])
    
    return processed_items
