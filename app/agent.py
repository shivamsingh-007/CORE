import os

import google.auth

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from app import tools

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

root_agent = Agent(
    name="root_agent",
    model=Gemini(model="gemini-flash-latest", retry_options=types.HttpRetryOptions(attempts=3)),
    instruction=(
        "You are a loop agent that enforces PLAN->IMPLEMENT->VERIFY development cycles. "
        "You can check if a project follows loop rules, scaffold loop files into a project, "
        "and read the current loop state. Always follow the loop rules yourself."
    ),
    tools=[
        tools.check_loop_compliance,
        tools.init_loop_project,
        tools.read_loop_state,
    ],
)

app = App(root_agent=root_agent, name="app")
