import os
import json
import time
from utils import fetch_sales_data, summarize_sales, parse_date_expression


CACHE_FILE = "cache_sales.json"
CACHE_TTL = 300 
MODEL = "gpt-4o-mini"


LLM_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
LLM_PROVIDER = "openai" if os.getenv("OPENAI_API_KEY") else ("anthropic" if os.getenv("ANTHROPIC_API_KEY") else None)

if LLM_PROVIDER == "openai":
    import openai
elif LLM_PROVIDER == "anthropic":
    from anthropic import Anthropic
    anthropic_client = Anthropic(api_key=LLM_API_KEY)

conversation_history = []

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            try:
                cache = json.load(f)
                if time.time() - cache.get("timestamp", 0) < CACHE_TTL:
                    print(" Using cached API data.")
                    return cache.get("data", [])
            except Exception:
                pass
    return []


def save_cache(data):
    with open(CACHE_FILE, "w") as f:
        json.dump({"timestamp": time.time(), "data": data}, f)


def analyze_with_llm(prompt, data_summary):
    global conversation_history

    if not LLM_PROVIDER or not LLM_API_KEY:
      
        items = data_summary.get("item_counts", {})
        if "best" in prompt.lower() or "most" in prompt.lower():
            if items:
                best_item = max(items, key=items.get)
                return f"The best-selling item is '{best_item}' with {items[best_item]} sales."
            return "No sales data found."
        elif "item" in prompt.lower() or "product" in prompt.lower():
            if not items:
                return "No items found in recent orders."
            item_list = "\n".join([f"- {k}: {v} sold" for k, v in items.items()])
            return f"Sales per item:\n{item_list}"
        elif "average" in prompt.lower():
            return f"Average order value: ${data_summary['avg_order_value']}."
        elif "revenue" in prompt.lower() or "sales" in prompt.lower():
            return f"Total revenue: ${data_summary['total_revenue']} from {data_summary['total_orders']} orders."
        else:
            return f"There were {data_summary['total_orders']} orders totaling ${data_summary['total_revenue']}."

    if LLM_PROVIDER == "openai":
        try:
            openai.api_key = LLM_API_KEY
            conversation_history.append({"role": "user", "content": prompt})

            response = openai.ChatCompletion.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful sales analyst. Use the provided sales summary to answer clearly and briefly."},
                    {"role": "user", "content": f"Sales summary: {json.dumps(data_summary)}"},
                    *conversation_history,
                ],
            )
            answer = response.choices[0].message.content.strip()
            conversation_history.append({"role": "assistant", "content": answer})
            return answer
        except Exception as e:
            return f" LLM Error: {e}"

    elif LLM_PROVIDER == "anthropic":
        try:
            response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=400,
                messages=[
                    {"role": "user", "content": f"Sales summary: {json.dumps(data_summary)}\n\nUser question: {prompt}"}
                ],
            )
            return response.content[0].text.strip()
        except Exception as e:
            return f" LLM Error: {e}"


def filter_orders_by_date(orders, start_date, end_date):
    filtered = []
    for order in orders:
        created = order.get("createdTime") or order.get("created_at") or order.get("created")
        if not created:
            continue
        created_date = created.split("T")[0] if "T" in created else created.split(" ")[0]
        if start_date <= created_date <= end_date:
            filtered.append(order)
    return filtered

def main():
    print("\n Sales Insight Agent — MKonnekt Sandbox API Integration\n")
    print("Ask questions like:\n  - What was the revenue yesterday?\n  - Which product sold the most?\n  - Show me all sales per item.\nType 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        start_date, end_date = parse_date_expression(user_input)
        print(f"Date range considered: {start_date} → {end_date}")

        orders = load_cache()
        if not orders:
            orders = fetch_sales_data()

        if not orders:
            print(" No orders returned from API.")
            continue

        save_cache(orders)

        filtered_orders = filter_orders_by_date(orders, start_date, end_date)
        if not filtered_orders:
            print(" No orders found for the selected date range.")
            continue

        summary = summarize_sales(filtered_orders)
        answer = analyze_with_llm(user_input, summary)
        print(f"\n  Agent: {answer}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n Interrupted by user. Goodbye!")
