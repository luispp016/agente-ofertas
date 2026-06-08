import requests
from bs4 import BeautifulSoup
import urllib.parse
import logging
import re

logger = logging.getLogger(__name__)

def search_amazon(query, domain="com"):
    """
    Searches Amazon (default amazon.com) using BeautifulSoup.
    Returns a list of dictionaries with product details.
    """
    encoded_query = urllib.parse.quote_plus(query)
    # Using amazon.com (Global/Colombia) by default
    url = f"https://www.amazon.{domain}/s?k={encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1"
    }
    
    results = []
    try:
        logger.info(f"Searching Amazon.{domain} for: {query}")
        response = requests.get(url, headers=headers, timeout=15)
        
        if "api-services-support@amazon.com" in response.text or "captcha" in response.text.lower():
            logger.warning("Amazon returned a CAPTCHA or block page. Skipping Amazon search for this run.")
            return results
            
        if response.status_code != 200:
            logger.warning(f"Amazon returned status code {response.status_code}")
            return results
            
        logger.info(f"Amazon response status: {response.status_code}, content size: {len(response.text)}")
        soup = BeautifulSoup(response.text, "html.parser")
        # Find all search result items
        items = soup.select('div[data-component-type="s-search-result"]')
        logger.info(f"Raw items selected by div[data-component-type='s-search-result']: {len(items)}")
        
        for item in items:
            # 1. Get Title
            title_el = item.select_one('h2')
            if not title_el:
                title_el = item.select_one('.a-size-medium, .a-size-base-plus')
            if not title_el:
                continue
            title = title_el.text.strip()
            
            # 2. Get URL
            link_el = item.select_one('a[href*="/dp/"]')
            if not link_el:
                link_el = item.select_one('h2 a')
            if not link_el or not link_el.get('href'):
                continue
            href = link_el.get('href')
            full_url = f"https://www.amazon.{domain}" + href if href.startswith('/') else href
            # Clean up URL (remove tracking parameters)
            full_url = full_url.split('/ref=')[0]
            
            # 3. Get Price
            price_el = item.select_one('.a-price .a-offscreen')
            if not price_el:
                continue # Skip items without price
            
            price_text = price_el.text.strip()
            # Extract numerical value from price text
            # E.g. "$299.99" -> 299.99 or "299,99 €" -> 299.99
            price_cleaned = re.sub(r'[^\d.,]', '', price_text)
            
            # Decide currency
            currency = "USD"
            price_text_lower = price_text.lower()
            if "cop" in price_text_lower or "col$" in price_text_lower:
                currency = "COP"
            elif "€" in price_text or "eur" in price_text_lower:
                currency = "EUR"
            elif "$" in price_text:
                if domain == "com.co":
                    currency = "COP"
                else:
                    currency = "USD" # default for amazon.com
            
            # Fix decimal separators for different locales
            if ',' in price_cleaned and '.' in price_cleaned:
                price_cleaned = price_cleaned.replace(',', '') # e.g. 1,234.56 -> 1234.56
            elif ',' in price_cleaned:
                # E.g., 299,99 -> 299.99
                # If comma is followed by 2 digits, it's likely decimal
                parts = price_cleaned.split(',')
                if len(parts[-1]) == 2:
                    price_cleaned = '.'.join(parts)
                else:
                    price_cleaned = ''.join(parts) # thousands separator
                    
            try:
                price = float(price_cleaned)
            except ValueError:
                continue
                
            # 4. Get Image
            image_el = item.select_one('.s-image')
            image_url = image_el.get('src') if image_el else ""
            
            results.append({
                "title": title,
                "price": price,
                "original_price": None,
                "currency": currency,
                "url": full_url,
                "image": image_url,
                "store": f"Amazon",
                "free_shipping": "free shipping" in item.text.lower() or "envío gratis" in item.text.lower(),
                "condition": "new"
            })
            
        logger.info(f"Found {len(results)} items on Amazon")
    except Exception as e:
        logger.error(f"Error scraping Amazon: {e}")
        
    return results
