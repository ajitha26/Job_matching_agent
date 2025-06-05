import pandas as pd
from google.adk.agents import Agent
import os, certifi
os.environ["SSL_CERT_FILE"] = certifi.where()
# Load the internship data
internships_df = pd.read_csv("internships_scraped.csv")
internships_data = internships_df.to_dict(orient="records")

# Tool function that the agent will use
def match_jobs_intelligent(skills: list[str]) -> dict:
    """
    Use LLM to recommend top 3 internships by analyzing descriptions and skill requirements.
    """
    # Format each internship for context
    internship_context = ""
    for i, row in enumerate(internships_data):
        internship_context += (
            f"\nInternship {i+1}:\n"
            f"Role: {row['role']}\n"
            f"Company: {row['company']}\n"
            f"Stipend: {row['stipend']}\n"
            f"Job Description: {row.get('job_description', '')}\n"
            f"Required Skills: {row.get('skills', '')}\n"
        )

    # Build prompt
    prompt = (
        f"You are a helpful assistant helping users find internships.\n"
        f"Given the following internships:\n{internship_context}\n\n"
        f"And a user with the following skills: {', '.join(skills)}\n"
        f"Recommend the top 3 internships that best match the user's skills. "
        f"Justify each recommendation based on job description and required skills."
    )

    # This part sends the prompt to the agent’s model
    # Assuming ADK handles that when invoked, we return the prompt for the LLM to process
    return {
        "status": "success",
        "prompt": prompt,
        "message": f"Prompt sent for matching based on skills {skills}.",
    }

# Define the agent
root_agent = Agent(
    name="job_matching_agent",
    model="gemini-2.0-flash",
    description="Agent to match user skills with the best internship roles based on job descriptions and required skills.",
    instruction="Read internship details and recommend top 3 matches for given skills.",
    tools=[match_jobs_intelligent],
)