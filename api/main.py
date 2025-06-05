from fastapi import FastAPI
import mysql.connector
import os
import sys
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from agents.agent import get_recommendations 
from agents.agent import root_agent 
from google.adk.agents.invocation_context import InvocationContext
from crawlers.job_scraper import run_list_scraper
from job_detail_scraper import run_detail_scraper
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

# ---- Session and Runner Setup ----
session_service = InMemorySessionService()
APP_NAME = "job_matching_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

session = None  # Global placeholder



runner = Runner(agent=root_agent,app_name=APP_NAME,session_service=session_service)

app = FastAPI()
# ✅ Allow CORS for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:5173"] if you're using Vite
    allow_credentials=True,
    allow_methods=["*"],  # or ["POST"]
    allow_headers=["*"],
)
def get_db_connection():
    return mysql.connector.connect(
        host="your_host",
        user="your_user",
        password="your_password",
        database="your_db"
    )
@app.on_event("startup")
async def startup_event():
    global session
    session = await session_service.create_session(app_name=APP_NAME,user_id=USER_ID)
@app.post("/scrape_and_store/")
async def scrape_and_store():
    # Step 1: Run listing scraper to get internships list and save CSV
    jobs_list = run_list_scraper()

    # Step 2: Run details scraper to get detailed info from saved CSV
    detailed_df = run_detail_scraper()

    # Step 3: Insert detailed internships into MySQL
    conn = get_db_connection()
    cursor = conn.cursor()

    for _, row in detailed_df.iterrows():
        cursor.execute("""
            INSERT INTO internships (role, company, stipend, link, job_description, skills, openings, perks, company_website, company_about)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                stipend=VALUES(stipend),
                job_description=VALUES(job_description),
                skills=VALUES(skills),
                openings=VALUES(openings),
                perks=VALUES(perks),
                company_website=VALUES(company_website),
                company_about=VALUES(company_about)
        """, (
            row['role'],
            row['company'],
            row['stipend'],
            row['link'],
            row.get('job_description', None),
            ','.join(row.get('skills', [])) if isinstance(row.get('skills'), list) else row.get('skills'),
            row.get('openings', None),
            ','.join(row.get('perks', [])) if isinstance(row.get('perks'), list) else row.get('perks'),
            row.get('company_website', None),
            row.get('company_about', None),
        ))

    conn.commit()
    cursor.close()
    conn.close()

    return {"message": f"Scraped {len(detailed_df)} internships and stored into DB."}

class SkillRequest(BaseModel):
    skills: List[str]

@app.post("/match_jobs/")
async def match_jobs(req: SkillRequest):
    return get_recommendations(req.skills)

class ChatMessage(BaseModel):
    role: str  # "user" or "agent"
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]

@app.post("/chat/")
async def chat_endpoint(payload: dict):
    user_input = payload.get("prompt", "")

    if not user_input:
        return {"error": "No prompt provided."}

    content = types.Content(role="user", parts=[types.Part(text=user_input)])

    final_response = "No response from agent."
    
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text
            break
    print(final_response)
    return {"response": final_response}
