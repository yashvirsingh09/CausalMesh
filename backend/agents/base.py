"""
agents/base.py — Model-agnostic LLM tool-calling loop.

This is the core engine shared by all three agents (Sentinel, Investigator,
Mitigator). It is intentionally NOT using LangChain or any agentic framework,
so you can see exactly what's happening at each step.

The loop:
  1. Send LLM a system prompt + context message
  2. LLM either returns a tool call or a final answer
  3. If tool call → execute the tool → feed result back to LLM → repeat
  4. Stream intermediate reasoning via an async callback

Supports: Groq, OpenAI, Google Gemini (selected via LLM_PROVIDER config)
"""
import json
import re
from typing import Callable, Awaitable, Any
from config import LLM_PROVIDER, LLM_MODEL, GROQ_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY


# ─── LLM CLIENT FACTORY ───────────────────────────────────────────────────────

def _make_groq_client():
    from groq import AsyncGroq
    return AsyncGroq(api_key=GROQ_API_KEY)


def _make_openai_client():
    from openai import AsyncOpenAI
    return AsyncOpenAI(api_key=OPENAI_API_KEY)


def _make_gemini_client():
    from openai import AsyncOpenAI
    return AsyncOpenAI(
        api_key=GOOGLE_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )


def _get_llm_client():
    provider = LLM_PROVIDER.lower()
    if provider == "groq":
        return _make_groq_client(), "groq"
    elif provider == "openai":
        return _make_openai_client(), "openai"
    elif provider in ("gemini", "google"):
        return _make_gemini_client(), "gemini"
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}. Use: groq | openai | gemini")


# ─── TOOL DEFINITION ──────────────────────────────────────────────────────────

class Tool:
    """
    Wraps a Python async function as an LLM-callable tool.
    The description and parameters are used to build the OpenAI-compatible
    tool spec sent to the LLM.
    """
    def __init__(self, name: str, description: str,
                 parameters: dict, fn: Callable[..., Awaitable[Any]]):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.fn = fn

    def to_spec(self) -> dict:
        """Returns OpenAI-compatible tool specification."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }

    async def execute(self, **kwargs) -> Any:
        return await self.fn(**kwargs)


# ─── AGENT LOOP ───────────────────────────────────────────────────────────────

StreamCallback = Callable[[str], Awaitable[None]]

MAX_ITERATIONS = 10   # Safety cap to prevent infinite loops


class AgentLoop:
    """
    A tight, transparent tool-calling loop.
    Every tool call, every graph query, every result is
    streamed back to the frontend via the stream callback.
    """

    def __init__(self, agent_name: str, system_prompt: str, tools: list[Tool]):
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.tools = {t.name: t for t in tools}
        self._client, self._provider = _get_llm_client()

    async def run(self, user_message: str,
                  stream: StreamCallback | None = None) -> str:
        """
        Runs the agent loop until the LLM produces a final answer
        (no more tool calls) or MAX_ITERATIONS is reached.

        Returns the final answer as a string.
        """

        async def _stream(msg: str):
            if stream:
                await stream(f"[{self.agent_name}] {msg}")

        await _stream(f"Starting... Input: {user_message[:120]}")

        messages = [
            {"role": "system",  "content": self.system_prompt},
            {"role": "user",    "content": user_message},
        ]

        tool_specs = [t.to_spec() for t in self.tools.values()]

        for iteration in range(MAX_ITERATIONS):
            # Call the LLM
            response = await self._chat(messages, tool_specs)

            # Check if it's a final answer (no tool calls)
            if not response.get("tool_calls"):
                final = response.get("content", "")
                await _stream(f" Final answer produced")
                return final

            # Append assistant message with all tool calls ONCE before results
            messages.append({
                "role": "assistant",
                "content": response.get("content"),
                "tool_calls": response["tool_calls"],
            })

            # Process each tool call
            for tc in response["tool_calls"]:
                fn_name = tc["function"]["name"]
                try:
                    fn_args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    fn_args = {}

                await _stream(f" Calling tool: `{fn_name}({json.dumps(fn_args, indent=None)})`")

                tool = self.tools.get(fn_name)
                if tool is None:
                    tool_result = {"error": f"Tool '{fn_name}' not found in agent toolset."}
                else:
                    try:
                        tool_result = await tool.execute(**fn_args)
                    except Exception as e:
                        tool_result = {"error": str(e)}

                await _stream(f" Result: {json.dumps(tool_result)[:300]}")

                # Append tool result
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(tool_result),
                })

        await _stream(" Max iterations reached — returning last known state.")
        return messages[-1].get("content", "Max iterations reached.")

    async def _chat(self, messages: list[dict], tools: list[dict]) -> dict:
        """Dispatches to the correct LLM provider."""
        if self._provider == "groq":
            return await self._chat_groq(messages, tools)
        elif self._provider in ("openai", "gemini"):
            return await self._chat_openai(messages, tools)
        raise ValueError(f"Unknown provider: {self._provider}")

    async def _chat_groq(self, messages: list[dict], tools: list[dict]) -> dict:
        resp = await self._client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,
            temperature=0.1,
            max_tokens=2048,
        )
        msg = resp.choices[0].message
        return {
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in (msg.tool_calls or [])
            ] or None,
        }

    async def _chat_openai(self, messages: list[dict], tools: list[dict]) -> dict:
        resp = await self._client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,
            temperature=0.1,
            max_tokens=2048,
        )
        msg = resp.choices[0].message
        return {
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in (msg.tool_calls or [])
            ] or None,
        }
