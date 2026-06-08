import requests
from bs4 import BeautifulSoup
import urllib.parse
import logging
import json
import re

logger = logging.getLogger(__name__)

def search_aliexpress(query):
    """
    Searches AliExpress using BeautifulSoup.
    Returns a list of dictionaries with product details.
    """
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://www.aliexpress.com/w/wholesale-{encoded_query}.html"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,es;q=0.8"
    }
    
    results = []
    try:
        logger.info(f"Searching AliExpress for: {query}")
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code != 200:
            logger.warning(f"AliExpress returned status code {response.status_code}")
            return results
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # AliExpress often embeds product JSON data inside a script tag containing window._INITIAL_DATA_
        # Let's search for this script tag first, as it contains structured, unblocked data!
        script_tag = None
        for script in soup.find_all("script"):
            if script.string and "window._INITIAL_DATA_" in script.string:
                script_tag = script.string
                break
                
        if script_tag:
            try:
                # Extract the JSON string from the script content
                # Format: window._INITIAL_DATA_ = { ... };
                json_str_match = re.search(r'window\._INITIAL_DATA_\s*=\s*(\{.*?\});', script_tag)
                if json_str_match:
                    json_data = json.loads(json_str_match.group(1))
                    # Extract list of products from JSON structure
                    # The structure is usually deeply nested: json_data['mods']['itemList']['content']
                    items = (json_data.get("mods", {})
                                     .get("itemList", {})
                                     .get("content", []))
                    
                    for item in items:
                        # Extract data points
                        title = item.get("title", {}).get("displayTitle", "")
                        if not title:
                            continue
                            
                        # Price
                        price_val = 0.0
                        price_info = item.get("prices", {}).get("salePrice", {})
                        if price_info:
                            price_val = float(price_info.get("value", 0))
                        else:
                            price_info = item.get("price", {})
                            price_val = float(price_info.get("value", 0))
                            
                        currency = item.get("prices", {}).get("salePrice", {}).get("currencyCode", "USD")
                        
                        # URL
                        product_id = item.get("productId", "")
                        product_url = f"https://www.aliexpress.com/item/{product_id}.html" if product_id else ""
                        
                        # Image
                        image_url = item.get("image", {}).get("imgUrl", "")
                        if image_url and image_url.startswith("//"):
                            image_url = "https:" + image_url
                            
                        results.append({
                            "title": title,
                            "price": price_val,
                            "original_price": None,
                            "currency": currency,
                            "url": product_url,
                            "image": image_url,
                            "store": "AliExpress",
                            "free_shipping": "free shipping" in str(item).lower(),
                            "condition": "new"
                        })
            except Exception as e:
                logger.warning(f"Error parsing AliExpress initial data: {e}")
                
        # If no script data or extraction failed, try scraping standard HTML cards (fallback)
        if not results:
            # AliExpress listing container cards (sometimes class is search-item-card or similar)
            cards = soup.select('div[class*="search-item-card"], div[class*="multi--container"]')
            for card in cards:
                title_el = card.select_one('h1[class*="title"], div[class*="title"]')
                if not title_el:
                    continue
                title = title_el.text.strip()
                
                link_el = card.select_one('a')
                if not link_el or not link_el.get('href'):
                    continue
                href = link_el.get('href')
                full_url = "https:" + href if href.startswith('//') else href
                
                # Clean up URL
                full_url = full_url.split('?')[0]
                
                price_el = card.select_one('div[class*="price--current"]')
                if not price_el:
                    continue
                price_text = price_el.text.strip()
                price_cleaned = re.sub(r'[^\d.,]', '', price_text)
                
                currency = "USD"
                if "cop" in price_text.lower() or "$" in price_text:
                    currency = "COP" # or USD, depending on user settings
                    
                # Clean numerical price
                if ',' in price_cleaned and '.' in price_cleaned:
                    price_cleaned = price_cleaned.replace(',', '')
                elif ',' in price_cleaned:
                    parts = price_cleaned.split(',')
                    if len(parts[-1]) == 2:
                        price_cleaned = '.'.join(parts)
                    else:
                        price_cleaned = ''.join(parts)
                        
                try:
                    price = float(price_cleaned)
                except ValueError:
                    continue
                    
                img_el = card.select_one('img')
                image_url = ""
                if img_el:
                    image_url = img_el.get('src') or img_el.get('data-src') or ""
                    if image_url.startswith("//"):
                        image_url = "https:" + image_url
                        
                results.append({
                    "title": title,
                    "price": price,
                    "original_price": None,
                    "currency": currency,
                    "url": full_url,
                    "image": image_url,
                    "store": "AliExpress",
                    "free_shipping": "free shipping" in card.text.lower() or "envío gratis" in card.text.lower(),
                    "condition": "new"
                })
                
        logger.info(f"Found {len(results)} items on AliExpress")
    except Exception as e:
        logger.error(f"Error scraping AliExpress: {e}")
        
    return results
