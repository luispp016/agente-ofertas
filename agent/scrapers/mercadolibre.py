import os
import requests
import logging

logger = logging.getLogger(__name__)

def search_mercadolibre(query, site_id="MCO"):
    """
    Searches MercadoLibre (default Colombia: MCO) using the search API.
    Returns a list of dictionaries with product details.
    """
    url = f"https://api.mercadolibre.com/sites/{site_id}/search"
    params = {"q": query, "limit": 20}
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Check if a MercadoLibre Access Token is provided in env
    token = os.environ.get("MERCADOLIBRE_ACCESS_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
        logger.info("Using MercadoLibre Access Token for authentication.")
        
    results = []
    try:
        logger.info(f"Searching MercadoLibre ({site_id}) for: {query}")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            items = data.get("results", [])
            for item in items:
                # MercadoLibre gives free_shipping in the 'shipping' dictionary
                shipping = item.get("shipping", {})
                free_shipping = shipping.get("free_shipping", False)
                
                results.append({
                    "title": item.get("title"),
                    "price": float(item.get("price", 0)),
                    "original_price": float(item.get("original_price")) if item.get("original_price") else None,
                    "currency": item.get("currency_id", "COP"),
                    "url": item.get("permalink"),
                    "image": item.get("thumbnail"),
                    "store": "MercadoLibre",
                    "free_shipping": free_shipping,
                    "condition": item.get("condition", "new")
                })
            logger.info(f"Found {len(results)} items on MercadoLibre")
        else:
            logger.error(f"MercadoLibre API error: {response.status_code}")
    except Exception as e:
        logger.error(f"Error querying MercadoLibre API: {e}")
        
    return results
