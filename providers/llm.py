"""Provider abstraction for Groq and Microsoft Azure OpenAI."""
from functools import lru_cache

from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_ENDPOINT, GROQ_API_KEY, GROQ_MODEL, LLM_PROVIDER


@lru_cache(maxsize=1)
def _client():
    if LLM_PROVIDER == "azure_openai":
        if not (AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY and AZURE_OPENAI_DEPLOYMENT):
            raise RuntimeError("azure_openai selected but AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, and AZURE_OPENAI_DEPLOYMENT are required")
        from openai import AzureOpenAI
        return AzureOpenAI(azure_endpoint=AZURE_OPENAI_ENDPOINT, api_key=AZURE_OPENAI_API_KEY, api_version=AZURE_OPENAI_API_VERSION)
    from groq import Groq
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is required when LLM_PROVIDER=groq")
    return Groq(api_key=GROQ_API_KEY)


def model_name() -> str:
    return AZURE_OPENAI_DEPLOYMENT if LLM_PROVIDER == "azure_openai" else GROQ_MODEL


def chat_completion(*, messages, tools=None, tool_choice=None, stream=False, max_tokens=2048):
    kwargs = {"model": model_name(), "messages": messages, "stream": stream, "max_tokens": max_tokens}
    if tools is not None:
        kwargs["tools"] = tools
    if tool_choice is not None:
        kwargs["tool_choice"] = tool_choice
    return _client().chat.completions.create(**kwargs)
