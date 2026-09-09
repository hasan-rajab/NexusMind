"""AutoGen compatibility team for multi-agent enterprise solution design."""
from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_MODEL


async def run_autogen_team(task: str) -> str:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.conditions import MaxMessageTermination
    from autogen_agentchat.teams import RoundRobinGroupChat
    from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
    model_client = AzureOpenAIChatCompletionClient(azure_deployment=AZURE_OPENAI_DEPLOYMENT, model=AZURE_OPENAI_MODEL, api_version=AZURE_OPENAI_API_VERSION, azure_endpoint=AZURE_OPENAI_ENDPOINT, api_key=AZURE_OPENAI_API_KEY)
    analyst = AssistantAgent("business_analyst", model_client=model_client, description="Turns ambiguous client needs into testable requirements and success metrics.", system_message="Identify stakeholders, constraints, measurable outcomes, data sources, and governance needs.")
    architect = AssistantAgent("solution_architect", model_client=model_client, description="Designs secure Azure/Foundry implementation architectures.", system_message="Convert requirements into a production design using Foundry, Azure OpenAI, Azure AI Search, APIs, evaluation, observability, security, and deployment controls.")
    team = RoundRobinGroupChat([analyst, architect], termination_condition=MaxMessageTermination(4), max_turns=4)
    result = await team.run(task=task)
    await model_client.close()
    return "\n".join(str(getattr(message, "content", message)) for message in result.messages if getattr(message, "source", "") != "user")
