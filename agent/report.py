import os
import json
import datetime
from jinja2 import Template
from .notifier import format_price_cop

def generate_report(comparison_results, history_data, output_path="docs/index.html"):
    """
    Generates a beautiful HTML dashboard using the comparison results and price history.
    """
    # Create the output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    # Read the template file
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "report_template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()
        
    template = Template(template_content)
    
    # Format dates and prices for display
    products_summary = []
    
    for name, deals in comparison_results.items():
        if not deals:
            continue
            
        best_deal = deals[0]
        # Format the best deal prices
        best_deal_display = {
            "title": best_deal["title"],
            "price_cop_formatted": format_price_cop(best_deal["price_cop"]),
            "original_price_formatted": format_price_cop(best_deal["original_price"]) if best_deal.get("original_price") else None,
            "url": best_deal["url"],
            "image": best_deal["image"],
            "store": best_deal["store"],
            "free_shipping": best_deal.get("free_shipping", False)
        }
        
        # Format all deals for this product
        formatted_deals = []
        for deal in deals:
            formatted_deals.append({
                "title": deal["title"],
                "price_cop_formatted": format_price_cop(deal["price_cop"]),
                "url": deal["url"],
                "image": deal["image"],
                "store": deal["store"],
                "free_shipping": deal.get("free_shipping", False)
            })
            
        products_summary.append({
            "name": name,
            "best_deal": best_deal_display,
            "all_deals": formatted_deals
        })
        
    # Get current timestamp in friendly format
    now = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
    
    # Render HTML
    html_output = template.render(
        last_updated=now,
        products_summary=products_summary,
        history_json_str=json.dumps(history_data)
    )
    
    # Save the output file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_output)
        
    print(f"Report successfully generated and saved to: {output_path}")
