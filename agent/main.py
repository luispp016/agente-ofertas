import os
import json
import datetime
import logging
from dotenv import load_dotenv

# Load local .env file during development
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("AgenteOfertas")

from agent.currency import get_exchange_rates
from agent.scrapers import search_mercadolibre, search_amazon, search_ebay, search_aliexpress
from agent.analyzer import process_and_compare_deals
from agent.notifier import send_telegram_alert
from agent.report import generate_report

def main():
    logger.info("Starting AgenteOfertas run...")
    
    # 1. Load configuration
    config_path = "config.json"
    if not os.path.exists(config_path):
        logger.error(f"Configuration file {config_path} not found. Exiting.")
        return
        
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    target_currency = config.get("currency", "COP")
    fallback_rate = config.get("exchange_rate_fallback", 4000.0)
    
    # 2. Load history
    history_path = "history.json"
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            try:
                history_data = json.load(f)
            except json.JSONDecodeError:
                logger.warning("History file was corrupted, starting fresh.")
                history_data = {"last_updated": "", "products": {}}
    else:
        history_data = {"last_updated": "", "products": {}}
        
    if "products" not in history_data:
        history_data["products"] = {}
        
    # 3. Get Exchange Rates
    rates = get_exchange_rates(target_currency, fallback_rate)
    
    # 4. Scrape and process each product
    comparison_results = {}
    current_time_iso = datetime.datetime.now().isoformat()
    
    for product in config.get("products", []):
        name = product["name"]
        queries = product.get("search_queries", [name])
        logger.info(f"====== Processing product: {name} ======")
        
        all_scraped_items = []
        for query in queries:
            # Query MercadoLibre (Colombia)
            try:
                ml_items = search_mercadolibre(query, site_id="MCO")
                all_scraped_items.extend(ml_items)
            except Exception as e:
                logger.error(f"MercadoLibre scraper failed for {query}: {e}")
                
            # Query Amazon
            try:
                amazon_items = search_amazon(query)
                all_scraped_items.extend(amazon_items)
            except Exception as e:
                logger.error(f"Amazon scraper failed for {query}: {e}")
                
            # Query eBay
            try:
                ebay_items = search_ebay(query)
                all_scraped_items.extend(ebay_items)
            except Exception as e:
                logger.error(f"eBay scraper failed for {query}: {e}")
                
            # Query AliExpress
            try:
                aliexpress_items = search_aliexpress(query)
                all_scraped_items.extend(aliexpress_items)
            except Exception as e:
                logger.error(f"AliExpress scraper failed for {query}: {e}")
                
        # Filter and compare deals
        matched_deals = process_and_compare_deals(all_scraped_items, product, rates)
        comparison_results[name] = matched_deals
        
        if not matched_deals:
            logger.warning(f"No valid deals found for {name} after filters.")
            continue
            
        best_deal = matched_deals[0]
        best_price = best_deal["price_cop"]
        logger.info(f"Best deal for {name}: {best_deal['title']} at {best_price} COP on {best_deal['store']}")
        
        # Check history and decide if we send an alert
        prod_history = history_data["products"].setdefault(name, {"history": [], "best_deal": {}})
        history_list = prod_history.get("history", [])
        
        record_history = False
        price_changed = False
        old_price = None
        
        if not history_list:
            # First time seeing this product
            record_history = True
            price_changed = True
        else:
            last_record = history_list[-1]
            old_price = last_record["price"]
            # Alert only if it drops significantly (or any drop)
            if best_price < old_price:
                price_changed = True
                record_history = True
            elif best_price > old_price:
                # Price went up, record it but no alert
                record_history = True
            else:
                # Check if it has been more than 24 hours since the last entry to keep drawing the timeline
                try:
                    last_time = datetime.datetime.fromisoformat(last_record["timestamp"])
                    if (datetime.datetime.now() - last_time).total_seconds() >= 86400:
                        record_history = True
                except Exception:
                    record_history = True
                    
        # Update history
        if record_history:
            history_list.append({
                "timestamp": current_time_iso,
                "price": best_price,
                "store": best_deal["store"]
            })
            # Cap history points to last 50 entries to avoid bloating
            if len(history_list) > 50:
                history_list.pop(0)
                
        prod_history["history"] = history_list
        prod_history["best_deal"] = best_deal
        
        # Trigger Telegram Notification if config enables it
        if config.get("telegram_enabled", True) and price_changed:
            send_telegram_alert(
                product_name=name,
                best_deal=best_deal,
                all_deals=matched_deals,
                price_changed=price_changed,
                old_price=old_price
            )
            
    # 5. Save updated history database
    history_data["last_updated"] = current_time_iso
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history_data, f, indent=2, ensure_ascii=False)
        
    # 6. Generate HTML Report
    generate_report(comparison_results, history_data, output_path="docs/index.html")
    logger.info("AgenteOfertas run finished successfully!")

if __name__ == "__main__":
    main()
