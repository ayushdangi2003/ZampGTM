import os
from dotenv import load_dotenv
from google import genai
from tavily import TavilyClient

# 1. Load the secret keys from the .env file
load_dotenv()

print("Testing connections...\n")

try:
    # 2. Test Tavily Web Search
    print("Sending test query to Tavily...")
    tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    search_result = tavily_client.search(query="What is Zamp finance?", search_depth="basic")
    print(f"✅ Tavily Success! Found {len(search_result['results'])} web results.\n")

    # 3. Test Google Gemini AI
    print("Waking up Gemini...")
    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    # UPDATED: Using the latest model version requested by the API
    response = gemini_client.models.generate_content(
        model='gemini-3.6-flash',
        contents='Say exactly: "Hello, World! My AI brain is online and ready for the Zamp case study."'
    )
    print(f"✅ Gemini Success! The AI says: {response.text}\n")

except Exception as e:
    print(f"❌ An error occurred: {e}")