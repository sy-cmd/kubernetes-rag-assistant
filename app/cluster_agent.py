from typing import List, Optional, Tuple

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_groq import ChatGroq

from app.config import settings
from app.cluster_tools import list_pods, describe_pod, get_pod_logs, list_namespaces

TOOLS = [list_pods, describe_pod, get_pod_logs, list_namespaces]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}

SYSTEM_PROMPT = """You are a Kubernetes cluster troubleshooting assistant with read-only \
access to the cluster via tools: list_pods, describe_pod, get_pod_logs, list_namespaces.

Rules:
1. If a pod name or namespace isn't given, call list_pods first (it covers all namespaces \
by default) to find the exact name and namespace.
2. Once you learn a pod's namespace from list_pods or a prior tool call, reuse that exact \
namespace for every subsequent describe_pod/get_pod_logs call on that pod. Never guess or \
default to "default" - if you're unsure, call list_pods again rather than assume.
3. Call list_pods and list_namespaces at most once per investigation unless you have a \
specific reason to believe cluster state changed since your last call. Reuse results you \
already have instead of re-listing before every subsequent tool call.
4. If asked to check something across many pods (e.g. "logs of every pod"), prioritize pods \
that are not Running/Ready or have restarts > 0 - you have a limited number of tool-call \
rounds, so spend them on what's actually likely to be broken rather than exhaustively \
fetching logs for every healthy pod.
5. Ground every claim in what the tools actually returned - cite specific details (restart \
count, container state/reason, exact event messages, log lines). If the tools show nothing \
wrong, say so plainly instead of listing generic troubleshooting steps.
6. If asked something none of your tools can answer, say so directly instead of guessing or \
inferring a number from unrelated data (e.g. never confuse a pod count with a namespace count \
- use list_namespaces for namespace questions).
7. Only after stating the grounded diagnosis, suggest what a human operator should check or \
do next. You cannot take any action yourself, only read cluster state.
8. Use the prior conversation turns for context (e.g. "list them" refers to pods already \
discussed), but always re-verify current state with tools rather than assuming it hasn't \
changed."""


def get_llm():
    return ChatGroq(
        model=settings.cluster_chat_model,
        api_key=settings.groq_api_key,
        temperature=0
    ).bind_tools(TOOLS)


def query_cluster(
    question: str,
    history: Optional[List[dict]] = None,
    max_steps: int = 6
) -> Tuple[str, List[str]]:
    llm = get_llm()

    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for turn in history or []:
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))
    messages.append(HumanMessage(content=question))

    tools_used = []

    for _ in range(max_steps):
        response = llm.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            return response.content, tools_used

        for call in response.tool_calls:
            tools_used.append(call["name"])
            tool = TOOLS_BY_NAME.get(call["name"])
            result = tool.invoke(call["args"]) if tool else f"Unknown tool: {call['name']}"
            messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))

    return "Couldn't finish the investigation within the step limit — try a more specific question.", tools_used
