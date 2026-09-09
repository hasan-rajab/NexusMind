"""Microsoft Agent Framework + Foundry integration using keyless Azure authentication."""
from config import FOUNDRY_MODEL, FOUNDRY_PROJECT_ENDPOINT


async def run_foundry_agent(task: str) -> str:
    if not FOUNDRY_PROJECT_ENDPOINT:
        raise RuntimeError("FOUNDRY_PROJECT_ENDPOINT is required")
    from agent_framework import Agent
    from agent_framework.foundry import FoundryChatClient
    from azure.identity import DefaultAzureCredential
    agent = Agent(client=FoundryChatClient(project_endpoint=FOUNDRY_PROJECT_ENDPOINT, model=FOUNDRY_MODEL, credential=DefaultAzureCredential()), name="NexusMindEnterpriseAgent", instructions="Translate enterprise requirements into secure, grounded, measurable AI solutions. Use evidence, state assumptions, and never invent data.")
    result = await agent.run(task)
    return str(result)
