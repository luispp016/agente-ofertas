import requests
import logging

logger = logging.getLogger(__name__)

def get_exchange_rates(target_currency="COP", fallback_rate=4000.0):
    """
    Fetches the current exchange rate for USD to target_currency.
    Returns a dictionary with exchange rates relative to USD (e.g., {'USD': 1.0, 'COP': 4000.0, 'EUR': 0.92})
    """
    rates = {
        "USD": 1.0,
        "EUR": 0.92,  # approximate default
        target_currency: fallback_rate
    }
    
    try:
        # Fetching latest rates relative to USD
        url = "https://open.er-api.com/v6/latest/USD"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("result") == "success":
                fetched_rates = data.get("rates", {})
                rates["EUR"] = fetched_rates.get("EUR", rates["EUR"])
                rates[target_currency] = fetched_rates.get(target_currency, rates[target_currency])
                logger.info(f"Exchange rates updated successfully: 1 USD = {rates[target_currency]} {target_currency}")
            else:
                logger.warning("Exchange rate API returned success=false, using defaults.")
        else:
            logger.warning(f"Exchange rate API returned status code {response.status_code}, using defaults.")
    except Exception as e:
        logger.error(f"Error fetching exchange rates: {e}. Using fallback rate: {fallback_rate}")
        
    return rates

def convert_to_cop(price, currency, rates):
    """
    Converts a price in a given currency to COP based on USD relative rates.
    """
    if not price:
        return 0.0
    
    # Clean currency symbol/code
    currency = currency.upper().strip()
    if currency in ["$", "COP", "COL$"]:
        return float(price)
        
    # Convert to USD first, then to COP
    usd_rate = rates.get("USD", 1.0)
    eur_rate = rates.get("EUR", 0.92)
    cop_rate = rates.get("COP", 4000.0)
    
    if currency in ["USD", "US$", "U$S"]:
        return float(price) * cop_rate
    elif currency in ["EUR", "€"]:
        # price in EUR -> divide by EUR rate to get USD -> multiply by COP rate
        price_usd = float(price) / eur_rate
        return price_usd * cop_rate
    else:
        # If rate is directly in the rates dict (e.g., currency is target currency itself)
        if currency in rates:
            # Conversion: price / rates[currency] * rates['COP']
            return (float(price) / rates[currency]) * cop_rate
            
    # Default fallback: assume USD if not COP, and multiply by cop_rate
    return float(price) * cop_rate
