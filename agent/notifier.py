import os
import requests
import logging

logger = logging.getLogger(__name__)

def format_price_cop(price_cop):
    """
    Formats a numeric price into COP string representation.
    E.g. 1500000 -> "$1.500.000 COP"
    """
    return f"${price_cop:,.0f}".replace(",", ".")

def send_telegram_alert(product_name, best_deal, all_deals=None, price_changed=False, old_price=None):
    """
    Sends an HTML-formatted message to the user's Telegram chat.
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        logger.warning("Telegram Bot Token or Chat ID not configured. Skipping alert.")
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # Header
    title = f"🔔 <b>¡NUEVO PRECIO MÍNIMO! - {product_name}</b>" if price_changed else f"📢 <b>Oferta Encontrada: {product_name}</b>"
    
    # Best deal details
    store = best_deal.get("store", "Desconocido")
    price_str = format_price_cop(best_deal["price_cop"])
    original_price_str = ""
    if best_deal.get("original_price"):
        orig_cop = best_deal["original_price"]
        # Convert if needed (if ML, original is already in COP. If others, convert. Here we just print as is or format)
        original_price_str = f" (Antes: ~{format_price_cop(orig_cop)})"
        
    shipping_str = "✈️ Envío Gratis" if best_deal.get("free_shipping") else "📦 Envío no incluido"
    
    message = (
        f"{title}\n\n"
        f"💵 <b>Precio:</b> {price_str}{original_price_str}\n"
        f"🏪 <b>Tienda:</b> {store}\n"
        f"📋 <b>Item:</b> {best_deal['title']}\n"
        f"{shipping_str}\n\n"
    )
    
    if price_changed and old_price:
        savings = old_price - best_deal["price_cop"]
        message += f"📉 ¡Bajó {format_price_cop(savings)}! (Precio anterior: {format_price_cop(old_price)})\n\n"
        
    # Compare with other stores if available
    if all_deals and len(all_deals) > 1:
        message += "📊 <b>Comparativa en otras tiendas:</b>\n"
        seen_stores = {store}
        count = 0
        for deal in all_deals:
            d_store = deal.get("store")
            if d_store in seen_stores:
                continue
            seen_stores.add(d_store)
            count += 1
            deal_price_str = format_price_cop(deal["price_cop"])
            message += f"• {d_store}: {deal_price_str} (<a href='{deal['url']}'>Ver</a>)\n"
            if count >= 3: # limit to top 3 comparisons
                break
        message += "\n"
        
    message += f"🛒 <b>Compra aquí:</b> <a href='{best_deal['url']}'>Enlace del Producto</a>"
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info(f"Telegram alert sent successfully for: {product_name}")
            return True
        else:
            logger.error(f"Error sending Telegram message: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        
    return False
