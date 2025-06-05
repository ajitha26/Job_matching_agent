from agents.agent import JobFilterAgent
from agents.project_match_agent import ProjectMatchAgent
from environments.job_env import JobEnv
import json
if __name__ == "__main__":
    env = JobEnv()
    state = env.load_state()

    job_filter_agent = JobFilterAgent()
    state.update(job_filter_agent.act(state))

    project_match_agent = ProjectMatchAgent()
    state.update(project_match_agent.act(state))

    print("\n\nFinal Matches:")
    for match in state["job_matches"]:
        print(json.dumps(match, indent=2))