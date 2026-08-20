import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from google import genai
from google.genai import types
from tavily import TavilyClient

# 1. Load Environment Variables
load_dotenv()

# 2. Initialize Clients
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def run_gtm_research():
    print("🚀 Starting GTM Agent...")

    # Step A: Fetch a prospect from the database
    response = supabase.table("prospects").select("*").limit(1).execute()
    if not response.data:
        print("No prospects found in the database.")
        return
    
    prospect = response.data[0]
    print(f"👤 Prospect identified: {prospect['name']} at {prospect['company']} ({prospect['role']})")

    # Step B: Research the prospect and company using Tavily
    search_query = f"{prospect['name']} {prospect['company']} {prospect['role']} recent news funding hiring"
    print(f"🔍 Searching the web for: {search_query}")
    search_result = tavily_client.search(query=search_query, search_depth="basic")
    
    # Combine the search results into a single text block for the AI
    research_context = "\n".join([result['content'] for result in search_result['results']])

    # Step C: Ask Gemini to analyze the research and write drafts
    print("🧠 Gemini is analyzing signals and drafting outreach...")
    
    prompt = f"""
    You are an expert SDR. Review this web research for {prospect['name']}, {prospect['role']} at {prospect['company']}.
    Research: {research_context}
    
    Task:
    1. Identify the strongest business signal (e.g., hiring, funding, product launch). If none is found, note that as an edge case.
    2. Draft a highly personalized, short email based on that signal.
    3. Draft a concise LinkedIn InMail based on that signal.
    
    Return your response strictly in JSON format with these exact keys:
    "signal_found", "email_draft", "linkedin_draft", "edge_case_flag"
    (If no edge case, leave "edge_case_flag" as "none")
    """

    ai_response = gemini_client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    
    # Parse the JSON response from Gemini
    result_data = json.loads(ai_response.text)
    print("✅ Drafts generated successfully!")

    # Step D: Save the results to the database
    print("💾 Saving results to Supabase...")
    supabase.table("outreach_runs").insert({
        "prospect_id": prospect['id'],
        "status": "pending_review",
        "signal_found": result_data.get("signal_found"),
        "email_draft": result_data.get("email_draft"),
        "linkedin_draft": result_data.get("linkedin_draft"),
        "edge_case_flag": result_data.get("edge_case_flag")
    }).execute()

    print("🎉 Run complete! Check your Supabase dashboard.")

if __name__ == "__main__":
    run_gtm_research()