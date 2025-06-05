import json

class JobEnv:
    def load_state(self):
        with open("data/resume.md", "r") as f:
            resume = f.read()
        with open("data/my_projects.json", "r") as f:
            projects = json.load(f)

        job_listings = []
        import os
        for fname in os.listdir("data/job_listings"):
            with open(f"data/job_listings/{fname}", "r") as f:
                job_listings.append(json.load(f))

        return {"resume": resume, "projects": projects, "job_listings": job_listings}
