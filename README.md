# Sales Insight Agent — MKonnekt Sandbox API Integration

This is a command-line agent that answers natural-language questions about sales data using the MKonnekt Sandbox API and an LLM (GPT-4o or Claude 3.5).

---

## Features
- Fetches live order data from MKonnekt API  
- Understands naturallanguage queries  
- Summarizes revenue, order count, and best-selling items  
- Works even without an LLM key (fallback logic)  
- Includes caching and simple date parsing  

---

## Setup Instructions
1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
