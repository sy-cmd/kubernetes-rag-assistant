from typing import List, Tuple

from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_groq import ChatGroq

from app.config import settings
from app.cluster_tools import list_pods, describe_pod, get_pod_logs

TOOLS = [list_pods, describe_pod, get_pod_logs]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}

SYSTEM_PROMPT = """You are a Kubernetes cluster troubleshooting assistant with read-only \
access to the cluster via tools. Use list_pods, describe_pod, and get_pod_logs to \
investigate the user's question about pod/cluster state before answering.

Always base your answer on what the tools actually return - don't guess. If a pod name \
or namespace isn't given, use list_pods first to find it. Explain the root cause plainly \
and suggest what a human operator should check or do next; you cannot take any action \
yourself, only read cluster state."""


def get_llm():
    return ChatGroq(
        model=settings.chat_model,
        api_key=settings.groq_api_key,
        temperature=0
    ).bind_tools(TOOLS)


def query_cluster(question: str, max_steps: int = 6) -> Tuple[str, List[str]]:
    llm = get_llm()
    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=question)]
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
