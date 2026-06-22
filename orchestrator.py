"""
NexusMind Orchestrator
──────────────────────
Agent loop:
  1. Build messages from role system prompt + conversation history.
  2. First LLM call with tool definitions → model decides to answer
     directly OR call web_search / retrieve_user_data.
  3. If tools called: execute them, inject results, do final LLM call.
  4. Yield response chunks as an async generator (SSE-compatible).
"""

import json
import asyncio
from groq import Groq
from config import GROQ_MODEL, GROQ_API_KEY
from roles import get_system_prompt
from tools.web_search import web_search
from tools.rag import retrieve_user_data

# ── Groq client ───────────────────────────────────────────────────────────────
_groq = Groq(api_key=GROQ_API_KEY)

# ── Tool schemas (OpenAI function-calling format) ─────────────────────────────
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
                    "query": {
                        "type": "string",
                        "description": "Concise search query (3-8 words).",
                    }
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
                    "query": {
                        "type": "string",
                        "description": "What to look for in the user's data.",
                    },
                    "role": {
                        "type": "string",
                        "description": (
                            "Active role context for scoped retrieval "
                            "(assistant / trainer / researcher / consultant)."
                        ),
                    },
                },
                "required": ["query"],
            },
        },
    },
]

# ── Tool dispatcher ───────────────────────────────────────────────────────────

def _execute_tool(name: str, args: dict, active_role: str) -> str:
    if name == "web_search":
        return web_search(args["query"])
    if name == "retrieve_user_data":
        return retrieve_user_data(
            query=args["query"],
            role=args.get("role", active_role),
        )
    return f"Unknown tool: {name}"


# ── Main agent loop ───────────────────────────────────────────────────────────

async def stream(
    query: str,
    role: str,
    history: list[dict],
):
    """
    Async generator that yields response text chunks.
    history format: [{"role": "user"|"assistant", "content": "..."}]
    """
    loop = asyncio.get_event_loop()
    system_prompt = get_system_prompt(role)

    messages = (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": query}]
    )

    # ── Round 1: tool-use decision (non-streaming) ────────────────────────────
    def _first_call():
        return _groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=1024,
        )

    r1 = await loop.run_in_executor(None, _first_call)
    assistant_msg = r1.choices[0].message

    # ── Execute tools if requested ────────────────────────────────────────────
    if assistant_msg.tool_calls:
        # Add assistant's tool-call message
        messages.append({
            "role": "assistant",
            "content": assistant_msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in assistant_msg.tool_calls
            ],
        })

        # Execute each tool and add results
        for tc in assistant_msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = await loop.run_in_executor(
                None, _execute_tool, tc.function.name, args, role
            )
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

        # ── Round 2: final synthesis (streaming) ──────────────────────────────
        def _final_call():
            return _groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                stream=True,
                max_tokens=2048,
            )

        stream_response = await loop.run_in_executor(None, _final_call)
        for chunk in stream_response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    else:
        # No tools needed — stream the direct answer
        direct_content = assistant_msg.content or ""
        if direct_content:
            # Re-request as a streaming call for consistent UX
            def _stream_direct():
                return _groq.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=messages,
                    stream=True,
                    max_tokens=2048,
                )
            stream_response = await loop.run_in_executor(None, _stream_direct)
            for chunk in stream_response:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
