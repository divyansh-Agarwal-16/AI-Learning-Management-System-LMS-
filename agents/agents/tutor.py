"""Tutor Agent module for the Multi-Agent System.

Uses search tools to extract course materials and explain concepts, citing sources.
"""

import os
import structlog
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agents.state import AgentState
from agents.tools.rag_tools import search_course_docs

logger = structlog.get_logger()


async def tutor_node(state: AgentState) -> Dict[str, Any]:
    """Tutor agent node explaining concepts using course RAG resources.

    Args:
        state (AgentState): Unified graph state.

    Returns:
        Dict[str, Any]: State updates containing tutor response and next action path.
    """
    messages = state.get("messages", [])
    course_id = state.get("course_id")
    
    logger.info("tutor_node_entry", message_count=len(messages), course_id=course_id)
    
    # 1. Fetch last user message query
    user_query = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_query = msg.content
            break
            
    if not user_query:
        logger.warning("tutor_node_no_user_query")
        return {
            "messages": messages + [AIMessage(content="I couldn't find a question in our conversation history. How can I help you learn?")],
            "next_action": "orchestrator",
            "current_agent": "tutor"
        }
        
    # 2. Retrieve Course Context chunks
    logger.info("tutor_retrieval_start", query=user_query)
    context_chunks = await search_course_docs(user_query, course_id)
    
    # Add retrieved context to the state history
    context_str = "\n\n".join(context_chunks)
    
    # 3. Prompt Construction
    system_prompt = (
        "You are an empathetic, expert AI Tutor designed to help students learn.\n"
        "Explain the requested concepts thoroughly and check for understanding.\n"
        "Answer the question using the provided course context materials. Always cite the specific source file and page numbers "
        "at the end of statements where you pull information from a source, using standard formats (e.g. [Source: python_basics.txt, Page 2]).\n\n"
        "If the context materials do not contain sufficient details to answer the query, "
        "explain clearly that the available course materials do not contain this information, and answer to the best of your general knowledge."
    )
    
    user_prompt = (
        f"Retrieved Course Context:\n"
        f"{context_str}\n\n"
        f"Student Question: {user_query}\n\n"
        f"Educational Answer:"
    )
    
    # 4. Invoke LLM (or mock fallback if credentials are absent)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "mock-key-for-testing":
        logger.warning("tutor_llm_mock_fallback")
        mock_reply = (
            f"[Tutor Agent] Based on your question '{user_query}', here is an explanation. "
            "I could not retrieve live database entries because I'm running in mock mode. "
            "Please configure your OpenAI API Key to connect live models. [Source: System Fallback, Page 1]"
        )
        return {
            "messages": messages + [AIMessage(content=mock_reply)],
            "context": context_chunks,
            "next_action": "orchestrator",
            "current_agent": "tutor"
        }
        
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key,
            temperature=0.3
        )
        
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        logger.info("tutor_llm_success")
        return {
            "messages": messages + [response],
            "context": context_chunks,
            "next_action": "orchestrator",
            "current_agent": "tutor"
        }
    except Exception as e:
        logger.error("tutor_llm_failed", error=str(e))
        error_msg = f"Tutor is currently offline. Error details: {str(e)}"
        return {
            "messages": messages + [AIMessage(content=error_msg)],
            "next_action": "orchestrator",
            "current_agent": "tutor",
            "error": str(e)
        }
