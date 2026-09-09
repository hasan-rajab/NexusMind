"""Semantic Kernel agent adapter for Azure OpenAI."""
from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_ENDPOINT


async def run_semantic_kernel_agent(task: str) -> str:
    from semantic_kernel.agents import ChatCompletionAgent
    from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
    service = AzureChatCompletion(deployment_name=AZURE_OPENAI_DEPLOYMENT, endpoint=AZURE_OPENAI_ENDPOINT, api_key=AZURE_OPENAI_API_KEY)
    agent = ChatCompletionAgent(service=service, name="NexusMindSKAgent", instructions="Design grounded enterprise AI answers. Prefer retrieved evidence and explicitly call out missing information instead of guessing.")
    response = await agent.get_response(messages=task)
    return str(response)
