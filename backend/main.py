import os
import json
import random
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv
from google import genai
from google.genai import types
from tavily import TavilyClient

# 1. Environment & Database
load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI(title="SignalGraph GTM Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FIRST_NAMES = ["Sarah", "Michael", "David", "Emma", "James", "Chen", "Priya", "Alex", "Jessica", "Marcus", "Elena", "Tom", "Nina", "Sam", "Olivia", "Omar", "Lucas", "Maya", "Daniel", "Sophia"]
LAST_NAMES = ["Smith", "Kim", "Patel", "Garcia", "Johnson", "Lee", "Martinez", "Davis", "O'Connor", "Nguyen", "Cohen", "Singh", "Ali", "Wong", "Müller", "Dubois", "Taylor", "Anderson"]

def generate_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

# ----------------- RESILIENT GEMINI CALLER -----------------
def call_gemini(prompt: str, json_mode: bool = False) -> str:
    """Tries primary and secondary Gemini models to ensure 100% uptime."""
    models_to_try = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']
    last_exception = None

    for model_name in models_to_try:
        try:
            config = types.GenerateContentConfig(response_mime_type="application/json") if json_mode else None
            response = gemini_client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )
            if response and response.text:
                return response.text
        except Exception as e:
            print(f"⚠️ Warning: Model {model_name} call failed: {e}. Trying fallback...")
            last_exception = e
            continue

    raise last_exception or Exception("All Gemini models failed to respond.")

# ----------------- PYDANTIC REQUEST SCHEMAS -----------------
class ResearchRequest(BaseModel):
    prospect_id: str

class RefineRequest(BaseModel):
    prospect_id: str
    message_type: str  # 'email' | 'inmail' | 'connection_note' | 'cold_call'
    current_text: str
    instruction: str

class AddCompanyRequest(BaseModel):
    name: str
    headquarters: Optional[str] = "Global"

# ----------------- API ENDPOINTS -----------------

@app.get("/")
def read_root():
    return {"message": "SignalGraph API is active! 🚀", "status": "online"}

@app.get("/api/companies")
def get_companies():
    """Fetch all companies ordered by name."""
    response = supabase.table("companies").select("*").order("name").execute()
    return response.data

@app.get("/api/companies/{company_id}/org-chart")
def get_company_org_chart(company_id: str):
    """Fetch company metadata and all 30 prospects for the React Flow canvas."""
    comp_res = supabase.table("companies").select("*").eq("id", company_id).execute()
    if not comp_res.data:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company = comp_res.data[0]
    pros_res = supabase.table("prospects").select("*").eq("company_id", company_id).execute()
    
    return {
        "company": company,
        "prospects": pros_res.data
    }

@app.post("/api/research")
def research_prospect(req: ResearchRequest):
    """Run live web research and generate 4 outreach formats + strategic rationales."""
    # 1. Fetch prospect details
    pros_res = supabase.table("prospects").select("*").eq("id", req.prospect_id).execute()
    if not pros_res.data:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    prospect = pros_res.data[0]

    # 2. Live Web Search with Tavily
    search_query = f"{prospect['name']} {prospect['role']} at {prospect['company']} recent news, hiring, expansion, quarterly results 2026"
    try:
        search_result = tavily_client.search(query=search_query, search_depth="basic")
        research_context = "\n".join([r.get('content', '') for r in search_result.get('results', [])])
    except Exception as e:
        research_context = f"Company {prospect['company']} is scaling rapidly in enterprise technology."

    # 3. Prompt Gemini for 4-channel outreach + why reach out note
    prompt = f"""
    You are an elite Enterprise SDR and GTM Strategist. 
    Analyze this web research for:
    - Prospect: {prospect['name']}
    - Title: {prospect['role']}
    - Department: {prospect['department']}
    - Company: {prospect['company']}

    Web Research Context:
    {research_context}

    Generate high-converting, non-robotic, personalized outreach materials.
    Return STRICTLY valid JSON with these exact keys:
    1. "signal_found": 1-2 sentence crisp business trigger (funding, hiring, product launch, strategic shift).
    2. "why_reach_out": 2-3 sentences explaining why this signal specifically matters to a {prospect['role']} right now.
    3. "email_draft": Subject line + 3-paragraph punchy cold email.
    4. "linkedin_inmail": High-converting, short InMail message (<120 words).
    5. "connection_note": Short, context-rich connection note (MUST BE under 280 characters).
    6. "cold_call_script": 30-second phone opener with: Pattern Interrupt -> Relevant Hook -> Value Proposition -> Open-ended CTA.
    7. "edge_case_flag": "none" (or describe any ambiguity/conflicting signals found).
    """

    try:
        raw_ai_text = call_gemini(prompt, json_mode=True)
        result_data = json.loads(raw_ai_text)
    except Exception as e:
        print(f"Error in research synthesis: {e}")
        # Fallback if all calls fail
        result_data = {
            "signal_found": f"{prospect['company']} is expanding tech stack and team headcount across core divisions.",
            "why_reach_out": f"As {prospect['role']}, optimizing pipeline efficiency and operational velocity during expansion cycles is top priority.",
            "email_draft": f"Subject: Scaling {prospect['company']}'s GTM efficiency\n\nHi {prospect['name']},\n\nNoticed {prospect['company']}'s continuous growth in the enterprise market. Typically, leaders in your role face tooling fragmentation as teams scale.\n\nWe built SignalGraph to streamline account intelligence without manual overhead.\n\nOpen to a brief 7-minute exchange this Thursday?\n\nBest,\nAyush",
            "linkedin_inmail": f"Hi {prospect['name']} - saw {prospect['company']}'s impressive market momentum. We're helping enterprise leaders eliminate data blindspots in multi-threaded accounts. Would love to share brief notes on how teams like yours approach this.",
            "connection_note": f"Hi {prospect['name']}, following {prospect['company']}'s growth in enterprise tech. Would love to connect and share insights from our GTM research!",
            "cold_call_script": f"\"Hi {prospect['name']}, this is Ayush—I know I caught you out of the blue, do you have 30 seconds for why I called? ... I saw {prospect['company']}'s recent expansion and wanted to see how you're currently tackling rep ramp times and account visibility. How are you approaching that this quarter?\"",
            "edge_case_flag": "none"
        }

    # 4. Save to outreach_runs table
    try:
        supabase.table("outreach_runs").insert({
            "prospect_id": prospect['id'],
            "status": "drafted",
            "signal_found": result_data.get("signal_found", ""),
            "email_draft": result_data.get("email_draft", ""),
            "linkedin_draft": result_data.get("linkedin_inmail", ""),
            "edge_case_flag": result_data.get("edge_case_flag", "none")
        }).execute()
    except Exception as e:
        print(f"Logging run error: {e}")

    return result_data

@app.post("/api/refine")
def refine_outreach(req: RefineRequest):
    """Refine a specific outreach draft based on user instructions using AI."""
    pros_res = supabase.table("prospects").select("*").eq("id", req.prospect_id).execute()
    prospect = pros_res.data[0] if pros_res.data else {"name": "Prospect", "role": "Executive", "company": "Target Account"}

    prompt = f"""
    You are an elite enterprise B2B sales copywriter.
    
    Target Prospect: {prospect.get('name')}
    Role: {prospect.get('role')} at {prospect.get('company')}
    Channel Format: {req.message_type}

    CURRENT COPY:
    \"\"\"{req.current_text}\"\"\"

    USER REVISION INSTRUCTION:
    \"{req.instruction}\"

    RULES:
    1. Rewrite the CURRENT COPY to strictly fulfill the USER REVISION INSTRUCTION.
    2. If Channel Format is 'connection_note', keep the length strictly under 280 characters.
    3. If Channel Format is 'email', maintain a clean Subject line and punchy body structure.
    4. If Channel Format is 'inmail', keep it under 120 words.
    5. If Channel Format is 'cold_call', ensure it sounds like a natural spoken dialogue.
    6. Return ONLY the rewritten message text. Do NOT include markdown code blocks, backticks, or conversational commentary.
    """

    try:
        refined_text = call_gemini(prompt, json_mode=False).strip()
        # Clean off any enclosing quotes if returned by the LLM
        if refined_text.startswith('"""') and refined_text.endswith('"""'):
            refined_text = refined_text[3:-3].strip()
        elif refined_text.startswith('"') and refined_text.endswith('"'):
            refined_text = refined_text[1:-1].strip()
    except Exception as e:
        print(f"❌ Refine error encountered: {e}")
        # Rule-based fallback so we never return raw bracket notes
        if "shorter" in req.instruction.lower():
            lines = [l for l in req.current_text.split('\n') if l.strip()]
            refined_text = "\n\n".join(lines[:3]) if len(lines) > 3 else req.current_text
        elif "formal" in req.instruction.lower():
            refined_text = req.current_text.replace("Hi ", "Dear ").replace("Hey ", "Hello ")
        else:
            refined_text = req.current_text

    return {"refined_text": refined_text}

@app.post("/api/companies/add")
def add_new_company_with_org(req: AddCompanyRequest):
    """Dynamically research a new company and auto-synthesize a 30-person hierarchy."""
    comp_name = req.name.strip()
    hq = req.headquarters.strip() if req.headquarters else "Global"

    if not comp_name:
        raise HTTPException(status_code=400, detail="Company name is required")

    # 1. Insert Company into Supabase
    try:
        comp_res = supabase.table("companies").insert({
            "name": comp_name,
            "industry": "Technology",
            "headcount": random.randint(400, 8500)
        }).execute()
        company = comp_res.data[0]
        comp_id = company['id']
    except Exception as e:
        existing = supabase.table("companies").select("*").eq("name", comp_name).execute()
        if existing.data:
            company = existing.data[0]
            comp_id = company['id']
        else:
            raise HTTPException(status_code=500, detail=str(e))

    # 2. Live Web Search for actual C-Suite executives
    search_query = f"{comp_name} headquarters in {hq} current CEO, CRO, CTO names 2026"
    try:
        search_result = tavily_client.search(query=search_query, search_depth="basic")
        context = "\n".join([r.get('content', '') for r in search_result.get('results', [])])
    except Exception:
        context = ""

    prompt = f"""
    Extract the current CEO, CRO (or Chief Commercial/Sales Officer), and CTO of {comp_name} (HQ in {hq}) based on:
    {context}
    If unavailable or ambiguous, provide highly plausible real executive names.
    Return STRICTLY JSON:
    {{"CEO": "Name", "CRO": "Name", "CTO": "Name"}}
    """

    try:
        raw_json = call_gemini(prompt, json_mode=True)
        execs = json.loads(raw_json)
    except Exception:
        execs = {"CEO": generate_name(), "CRO": generate_name(), "CTO": generate_name()}

    # 3. Clean any existing prospects for this company
    supabase.table("prospects").delete().eq("company_id", comp_id).execute()

    # 4. Insert Hierarchy (30 people total)
    ceo_res = supabase.table("prospects").insert({
        "company_id": comp_id, "name": execs.get("CEO", generate_name()), "company": comp_name, "role": "CEO", "department": "Executive"
    }).execute()
    ceo_id = ceo_res.data[0]['id']

    cro_res = supabase.table("prospects").insert({
        "company_id": comp_id, "manager_id": ceo_id, "name": execs.get("CRO", generate_name()), "company": comp_name, "role": "CRO", "department": "Executive"
    }).execute()
    cro_id = cro_res.data[0]['id']

    supabase.table("prospects").insert({
        "company_id": comp_id, "manager_id": ceo_id, "name": execs.get("CTO", generate_name()), "company": comp_name, "role": "CTO", "department": "Executive"
    }).execute()

    vp_roles = ["VP of Sales", "VP of RevOps", "VP of Customer Success"]
    vp_ids = []
    for role in vp_roles:
        res = supabase.table("prospects").insert({
            "company_id": comp_id, "manager_id": cro_id, "name": generate_name(), "company": comp_name, "role": role, "department": "Sales"
        }).execute()
        vp_ids.append(res.data[0]['id'])

    vp_sales_id = vp_ids[0]
    for _ in range(4):
        dir_res = supabase.table("prospects").insert({
            "company_id": comp_id, "manager_id": vp_sales_id, "name": generate_name(), "company": comp_name, "role": "Director of Sales", "department": "Sales"
        }).execute()
        dir_id = dir_res.data[0]['id']

        for j in range(5):
            role = "Account Executive" if j < 2 else "SDR"
            supabase.table("prospects").insert({
                "company_id": comp_id, "manager_id": dir_id, "name": generate_name(), "company": comp_name, "role": role, "department": "Sales"
            }).execute()

    return {"company": company, "message": f"Successfully created {comp_name} with 30 leads and complete org structure!"}

@app.get("/api/runs")
def get_run_history():
    """Fetch the latest AI outreach runs and edge cases."""
    response = supabase.table("outreach_runs").select(
        "id, status, signal_found, edge_case_flag, created_at, prospects(name, company, role)"
    ).order("created_at", desc=True).limit(25).execute()
    return response.data