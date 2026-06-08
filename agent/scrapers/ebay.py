import requests
from bs4 import BeautifulSoup
import urllib.parse
import logging
import re

logger = logging.getLogger(__name__)

def search_ebay(query):
    """
    Searches eBay using BeautifulSoup.
    Returns a list of dictionaries with product details.
    """
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://www.ebay.com/sch/i.html?_nkw={encoded_query}&_ipg=24"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,es;q=0.8"
    }
    
    results = []
    try:
        logger.info(f"Searching eBay for: {query}")
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code != 200:
            logger.warning(f"eBay returned status code {response.status_code}")
            return results
            
        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select(".srp-results .s-item, .srp-main-content .s-item")
        
        for item in items:
            # Skip eBay's generic top banner item which is structured like an s-item
            if "s-item__pl-on-bottom" in item.get("class", []):
                # Often the first item is a placeholder, check if it has a real title
                title_el = item.select_one(".s-item__title")
                if title_el and "shop on ebay" in title_el.text.lower():
                    continue
            
            # 1. Get Title
            title_el = item.select_one(".s-item__title")
            if not title_el:
                continue
            title = title_el.text.strip()
            # Remove "New Listing" or other prefixes eBay adds
            title = re.sub(r'^(New Listing|Anuncio nuevo)\s+', '', title, flags=re.IGNORECASE)
            
            if not title or "shop on ebay" in title.lower():
                continue
                
            # 2. Get URL
            link_el = item.select_one(".s-item__link")
            if not link_el or not link_el.get("href"):
                continue
            full_url = link_el.get("href").split("?")[0] # clean URL
            
            # 3. Get Price
            price_el = item.select_one(".s-item__price")
            if not price_el:
                continue
            price_text = price_el.text.strip()
            
            # Handle ranges like "$20.00 to $30.00" - take the lower bound
            if " to " in price_text:
                price_text = price_text.split(" to ")[0]
            elif " a " in price_text:
                price_text = price_text.split(" a ")[0]
                
            # Extract digits and decimal point/comma
            # E.g. "COP 1,200,000.00" or "$349.99"
            currency = "USD"
            if "cop" in price_text.lower():
                currency = "COP"
            elif "eur" in price_text.lower() or "€" in price_text:
                currency = "EUR"
            elif "gbp" in price_text.lower() or "£" in price_text:
                currency = "GBP"
                
            price_cleaned = re.sub(r'[^\d.,]', '', price_text)
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
                
            # 4. Get Shipping cost
            shipping_el = item.select_one(".s-item__shipping, .s-item__logisticsCost")
            free_shipping = False
            if shipping_el:
                ship_text = shipping_el.text.lower()
                if "free" in ship_text or "gratis" in ship_text:
                    free_shipping = True
            
            # 5. Get Image
            image_el = item.select_one(".s-item__image-img")
            image_url = ""
            if image_el:
                # eBay lazy loads images, check data-src first
                image_url = image_el.get("data-src") or image_el.get("src") or ""
                
            results.append({
                "title": title,
                "price": price,
                "original_price": None,
                "currency": currency,
                "url": full_url,
                "image": image_url,
                "store": "eBay",
                "free_shipping": free_shipping,
                "condition": "new" if "new" in item.text.lower() else "used"
            })
            
        logger.info(f"Found {len(results)} items on eBay")
    except Exception as e:
        logger.error(f"Error scraping eBay: {e}")
        
    return results
