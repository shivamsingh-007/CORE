from google.adk.agents import Agent

from app.tools import (
    add_lesson,
    check_loop_compliance,
    init_loop_project,
    plan_next_step,
    read_loop_state,
    update_loop_state,
)

compliance_agent = Agent(
    name="compliance_agent",
    model="gemini-2.0-flash",
    instruction="""You check whether a project follows loop conventions.
Call check_loop_compliance with the project path, then explain which files
are missing and what needs to be created.""",
    description="Checks if a project follows loop file conventions.",
    tools=[check_loop_compliance],
)

scaffold_agent = Agent(
    name="scaffold_agent",
    model="gemini-2.0-flash",
    instruction="""You scaffold loop agent files into a project directory.
Call init_loop_project with the project path to create the standard loop files
(AGENTS.md, loop-rules.md, LOOP.md, context.md, state.md, tasks/).""",
    description="Creates loop agent project files (scaffolding).",
    tools=[init_loop_project],
)

state_agent = Agent(
    name="state_agent",
    model="gemini-2.0-flash",
    instruction="""You manage the loop state file (state.md).
- Use read_loop_state to show current state
- Use update_loop_state to record progress after each step

When updating state, ask the user what step they completed and the result.""",
    description="Reads and updates the project's loop state.",
    tools=[read_loop_state, update_loop_state],
)

planner_agent = Agent(
    name="planner_agent",
    model="gemini-2.0-flash",
    instruction="""You plan the next implementation step.
Call plan_next_step with the project path and the user's goal to analyze
current state and todo.md, then propose the next action.""",
    description="Analyzes state to determine the next step to work on.",
    tools=[plan_next_step],
)

lessons_agent = Agent(
    name="lessons_agent",
    model="gemini-2.0-flash",
    instruction="""You record lessons learned to prevent repeating mistakes.
Call add_lesson with context, what went wrong, and the rule to follow.
Ask the user for these details if not provided.""",
    description="Records lessons learned from failures or mistakes.",
    tools=[add_lesson],
)

root_agent = Agent(
    name="loop_agent",
    model="gemini-2.0-flash",
    instruction="""You are a loop agent that enforces PLAN->IMPLEMENT->VERIFY development cycles.

You have specialist sub-agents you can delegate to:
- compliance_agent: checks if a project follows loop conventions
- scaffold_agent: creates loop project files in a new directory
- state_agent: reads/updates the project state
- planner_agent: analyzes state and plans the next step
- lessons_agent: records lessons learned

When the user asks something, route to the right sub-agent by describing
what you need. You can also use your general knowledge for simple questions
about loop methodology.

Typical workflow:
1. User sets a goal -> delegate to planner_agent for next-step analysis
2. User completes a step -> delegate to state_agent to record progress
3. Something went wrong -> delegate to lessons_agent to record the lesson
4. User asks about project state -> delegate to state_agent to read state
5. User wants to check a new project -> delegate to compliance_agent
6. User wants to start a new project -> delegate to scaffold_agent
""",
    description="Root loop agent that orchestrates PLAN->IMPLEMENT->VERIFY cycles.",
    sub_agents=[
        compliance_agent,
        scaffold_agent,
        state_agent,
        planner_agent,
        lessons_agent,
    ],
)
