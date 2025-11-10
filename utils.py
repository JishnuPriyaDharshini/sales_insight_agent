import requests
from datetime import datetime, timedelta
import re


API_URL = "https://sandbox.mkonnekt.net/ch-portal/api/v1/orders/recent"


def fetch_sales_data(api_key=None, use_fake=False):
    
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        print(" Fetching live sales data from MKonnekt sandbox API...")
        response = requests.get(API_URL, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict):
            if "data" in data and isinstance(data["data"], list):
                data = data["data"]
            elif "orders" in data and isinstance(data["orders"], list):
                data = data["orders"]
            else:
                print(" Unexpected API format:", list(data.keys()))
                print(" Sample:", str(data)[:200])
                return []

        if not isinstance(data, list):
            print(" Unexpected API format — expected a list of orders.")
            print(" Sample:", str(data)[:200])
            return []

        print(f" Retrieved {len(data)} orders from API.")
        return data

    except Exception as e:
        print(f" Error fetching sales data: {e}")
        return []


def summarize_sales(data):
    
    if not isinstance(data, list) or len(data) == 0:
        return {
            "total_orders": 0,
            "total_revenue": 0,
            "avg_order_value": 0,
            "item_counts": {},
        }

    total_orders = 0
    total_revenue = 0
    item_counts = {}

    for order in data:
        try:
            if order.get("state") != "locked":
                continue 
            total_orders += 1
            total_revenue += float(order.get("total", 0)) / 100.0 

            for item in order.get("lineItems", []):
                name = item.get("name", "Unknown Item")
                item_counts[name] = item_counts.get(name, 0) + 1
        except Exception:
            continue

    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

    top_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)

    return {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "avg_order_value": round(avg_order_value, 2),
        "item_counts": dict(top_items),
    }


def parse_date_expression(text):
    
    today = datetime.now()
    text = text.lower()

    if "yesterday" in text:
        start = today - timedelta(days=1)
        end = today - timedelta(days=1)
    elif "last week" in text:
        start = today - timedelta(days=7)
        end = today
    elif "today" in text:
        start = today
        end = today
    else:
        start = today - timedelta(days=7)
        end = today

    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
