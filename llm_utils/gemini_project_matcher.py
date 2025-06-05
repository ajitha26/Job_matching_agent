def match_projects_to_jobs(projects, jobs):
    # Placeholder: match based on keyword overlap
    matches = []
    for job in jobs:
        for project in projects:
            if any(skill.lower() in project["description"].lower() for skill in job.get("required_skills", [])):
                matches.append({"job": job["title"], "project": project["title"]})
    return matches