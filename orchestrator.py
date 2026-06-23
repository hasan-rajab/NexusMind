"""
NexusMind Orchestrator
──────────────────────
Agent loop:
  1. Build messages from role system prompt + conversation history.
  2. First LLM call with tool definitions → model decides to answer
     directly OR call web_search / retrieve_user_data.
  3. If tools called: execute them, inject results, do final LLM call.
  4. Yield (turn_id, chunk) tuples — turn_id emitted once at start.
"""

import json
import uuid
import asyncio
from groq import Groq
from config import GROQ_MODEL, GROQ_API_KEY
from roles import get_system_prompt
from tools.web_search import web_search
from tools.rag import retrieve_user_data

_groq = Groq(api_key=GROQ_API_KEY)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the internet for current information, recent events, "
                "real-world data, news, research papers, or anything the model "
                "cannot answer confidently from memory."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Concise search query (3-8 words)."}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_user_data",
            "description": (
                "Retrieve relevant information from the user's personal "
                "knowledge base: their notes, goals, workout logs, saved "
                "documents, or any previously stored context."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to look for in the user's data."},
                    "role":  {"type": "string", "description": "Active role for scoped retrieval."},
                },
                "required": ["query"],
            },
        },
    },
]


def _execute_tool(name: str, args: dict, active_role: str) -> str:
    if name == "web_search":
        return web_search(args["query"])
    if name == "retrieve_user_data":
        return retrieve_user_data(query=args["query"], role=args.get("role", active_role))
    return f"Unknown tool: {name}"


async def stream(query: str, role: str, history: list[dict]):
    """
    Async generator yielding dicts:
      {"turn_id": str}           — first item, always
      {"chunk": str}             — response text chunks
      {"tools_used": list[str]}  — after tool execution (may be absent)
    """
    loop       = asyncio.get_event_loop()
    turn_id    = str(uuid.uuid4())
    tools_used = []

    yield {"turn_id": turn_id}

    system_prompt = get_system_prompt(role)
    messages = (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": query}]
    )

    # ── Round 1: tool-use decision ────────────────────────────────────────────
    def _first_call():
        return _groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=1024,
        )

    r1            = await loop.run_in_executor(None, _first_call)
    assistant_msg = r1.choices[0].message

    # ── Execute tools if requested ────────────────────────────────────────────
    if assistant_msg.tool_calls:
        messages.append({
            "role":    "assistant",
            "content": assistant_msg.content or "",
            "tool_calls": [
                {
                    "id":   tc.id,
                    "type": "function",
                    "function": {
                        "name":      tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in assistant_msg.tool_calls
            ],
        })

        for tc in assistant_msg.tool_calls:
            args   = json.loads(tc.function.arguments)
            result = await loop.run_in_executor(
                None, _execute_tool, tc.function.name, args, role
            )
            tools_used.append(tc.function.name)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        yield {"tools_used": tools_used}

        def _final_call():
            return _groq.chat.completions.create(
                model=GROQ_MODEL, messages=messages, stream=True, max_tokens=2048,
            )

        stream_resp = await loop.run_in_executor(None, _final_call)
        for chunk in stream_resp:
            delta = chunk.choices[0].delta.content
            if delta:
                yield {"chunk": delta}

    else:
        def _stream_direct():
            return _groq.chat.completions.create(
                model=GROQ_MODEL, messages=messages, stream=True, max_tokens=2048,
            )
        stream_resp = await loop.run_in_executor(None, _stream_direct)
        for chunk in stream_resp:
            delta = chunk.choices[0].delta.content
            if delta:
                yield {"chunk": delta}
