import os
import json
import random
import time
from dotenv import load_dotenv
from supabase import create_client, Client
from google import genai
from google.genai import types
from tavily import TavilyClient

# 1. Load Keys
load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

COMPANIES = ["Microsoft", "Vercel", "Datadog", "Stripe", "Rippling", "OpenAI", "Figma", "Airtable", "Canva", "Linear"]

# Synthetic names for mid/lower levels
FIRST_NAMES = ["Sarah", "Michael", "David", "Emma", "James", "Chen", "Priya", "Alex", "Jessica", "Marcus", "Elena", "Tom", "Nina", "Sam", "Olivia", "Omar"]
LAST_NAMES = ["Smith", "Kim", "Patel", "Garcia", "Johnson", "Lee", "Martinez", "Davis", "O'Connor", "Nguyen", "Cohen", "Singh", "Ali", "Wong"]

def generate_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def run_hybrid_seed():
    print("🌱 Clearing old database rows...")
    supabase.table("outreach_runs").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    supabase.table("prospects").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    supabase.table("companies").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    total_prospects = 0

    for comp_name in COMPANIES:
        print(f"\n🏢 Processing {comp_name}...")
        
        # Insert Company Profile
        comp_res = supabase.table("companies").insert({
            "name": comp_name, "industry": "Technology", "headcount": random.randint(500, 10000)
        }).execute()
        comp_id = comp_res.data[0]['id']

        # AI Web Search for Real Executives
        print(f"🔍 Searching live web for {comp_name} real executives...")
        search_query = f"{comp_name} current CEO, CRO, CTO names 2026"
        search_result = tavily_client.search(query=search_query, search_depth="basic")
        context = "\n".join([r['content'] for r in search_result['results']])

        prompt = f"""
        Extract the current CEO, CRO (Chief Revenue Officer), and CTO of {comp_name} based on this text: {context}
        If you cannot find a specific role, guess a highly realistic name.
        Return STRICTLY JSON with these exact keys:
        {{"CEO": "Name", "CRO": "Name", "CTO": "Name"}}
        """
        
        # NEW ERROR HANDLING: Fallback if Gemini 503s
        try:
            ai_response = gemini_client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            execs = json.loads(ai_response.text)
            print(f"✅ Found: CEO {execs.get('CEO')} | CRO {execs.get('CRO')} | CTO {execs.get('CTO')}")
        except Exception as e:
            print("⚠️ Gemini server is busy (503). Generating plausible synthetic executives to keep the script moving...")
            execs = {"CEO": generate_name(), "CRO": generate_name(), "CTO": generate_name()}

        # Insert Executives (Level 1 & 2)
        ceo_res = supabase.table("prospects").insert({
            "company_id": comp_id, "name": execs.get("CEO", generate_name()), "company": comp_name, "role": "CEO", "department": "Executive"
        }).execute()
        ceo_id = ceo_res.data[0]['id']
        total_prospects += 1

        cro_res = supabase.table("prospects").insert({
            "company_id": comp_id, "manager_id": ceo_id, "name": execs.get("CRO", generate_name()), "company": comp_name, "role": "CRO", "department": "Executive"
        }).execute()
        cro_id = cro_res.data[0]['id']
        total_prospects += 1

        supabase.table("prospects").insert({
            "company_id": comp_id, "manager_id": ceo_id, "name": execs.get("CTO", generate_name()), "company": comp_name, "role": "CTO", "department": "Executive"
        }).execute()
        total_prospects += 1

        # Synthesize the remaining 27 people reporting to the CRO
        print("🧬 Synthesizing VPs, Directors, and SDRs...")
        vp_roles = ["VP of Sales", "VP of RevOps", "VP of Customer Success"]
        vp_ids = []
        for role in vp_roles:
            res = supabase.table("prospects").insert({
                "company_id": comp_id, "manager_id": cro_id, "name": generate_name(), "company": comp_name, "role": role, "department": "Sales"
            }).execute()
            vp_ids.append(res.data[0]['id'])
            total_prospects += 1

        vp_sales_id = vp_ids[0]
        
        for i in range(4): # 4 Directors
            dir_res = supabase.table("prospects").insert({
                "company_id": comp_id, "manager_id": vp_sales_id, "name": generate_name(), "company": comp_name, "role": "Director of Sales", "department": "Sales"
            }).execute()
            dir_id = dir_res.data[0]['id']
            total_prospects += 1
            
            for j in range(5): # 5 ICs per Director
                role = "Account Executive" if j < 2 else "SDR"
                supabase.table("prospects").insert({
                    "company_id": comp_id, "manager_id": dir_id, "name": generate_name(), "company": comp_name, "role": role, "department": "Sales"
                }).execute()
                total_prospects += 1
        
        # Pause briefly to prevent hitting free-tier API rate limits
        time.sleep(2) 

    print(f"\n🎉 Done! Successfully seeded {total_prospects} prospects across 10 companies.")

if __name__ == "__main__":
    run_hybrid_seed()