from typing import Tuple

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

from app.config import settings
from app.retrieval import retrieve_chunks, format_sources


def get_llm():
    return ChatGroq(
        model=settings.chat_model,
        api_key=settings.groq_api_key,
        temperature=0.3
    )


SYSTEM_PROMPT = """You are an expert Kubernetes and k3s assistant. Use the context provided from the user's documentation to answer their question accurately and concisely.

If the context doesn't contain enough information to fully answer the question, say so but still provide what's available.

Format your response clearly with:
- Direct answer to the question
- Relevant commands (in code blocks)
- Source reference at the end

Context from documentation:
{context}"""


USER_PROMPT = """Question: {input}

Provide a helpful answer based on the documentation."""


def query_rag(question: str, top_k: int = 5) -> Tuple[str, list, int]:
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", USER_PROMPT)
    ])

    docs = retrieve_chunks(question, top_k)

    if not docs:
        return "I couldn't find relevant information in the documentation. Try rephrasing your question.", [], 0

    sources = format_sources(docs)

    context = "\n\n".join([doc.page_content for doc in docs])

    response = llm.invoke(prompt.format(context=context, input=question))

    return response.content, sources, len(docs)