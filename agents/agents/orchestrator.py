"""Orchestrator Agent module for the Multi-Agent System.

Parses user messages, makes routing classifications, and coordinates agent transitions.
"""

import os
import json
import structlog
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agents.state import AgentState

logger = structlog.get_logger()


async def orchestrator_node(state: AgentState) -> Dict[str, Any]:
    """Orchestrates routing decisions based on user intent and graph turn progress.

    Args:
        state (AgentState): Unified graph state.

    Returns:
        Dict[str, Any]: State updates with target next_action.
    """
    messages = state.get("messages", [])
    
    # Log current state details
    logger.info(
        "orchestrator_node_entry",
        message_count=len(messages),
        last_agent=state.get("current_agent"),
        prev_action=state.get("next_action")
    )
    
    # 1. Turn Resolution Check:
    # If the last message is an AIMessage, it implies a specialized agent has
    # already responded to the user's latest question. We terminate the turn.
    if messages and isinstance(messages[-1], AIMessage):
        logger.info("orchestrator_turn_concluded", last_message_type="AIMessage")
        return {
            "next_action": "end",
            "current_agent": "orchestrator"
        }
        
    # 2. Intent Classification via LLM:
    # If the last message is from the user (HumanMessage), determine routing.
    user_query = messages[-1].content if messages else ""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "mock-key-for-testing":
        # Fallback heuristic router if LLM is unavailable
        logger.warning("orchestrator_heuristic_fallback", query=user_query)
        query_lower = user_query.lower()
        
        if "quiz" in query_lower or "test" in query_lower or "exam" in query_lower or "approve" in query_lower or "yes" in query_lower:
            next_action = "quiz_generator"
        elif "progress" in query_lower or "plan" in query_lower or "schedule" in query_lower or "next" in query_lower:
            next_action = "path_advisor"
        else:
            next_action = "tutor"
            
        logger.info("orchestrator_heuristic_route", next_action=next_action)
        return {
            "next_action": next_action,
            "current_agent": "orchestrator"
        }

    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key,
            temperature=0.0
        )
        
        system_prompt = (
            "You are the central Orchestrator for an AI Learning Management System.\n"
            "Analyze the user's latest request and decide which specialized agent to route to:\n"
            "- \"tutor\": For learning concepts, asking academic questions, explaining code, clarifying doubts, or general learning conversation.\n"
            "- \"quiz_generator\": If the user wants to generate a quiz, check their knowledge, requests mock tests, or is responding to/approving a generated quiz.\n"
            "- \"path_advisor\": If the user asks about their course progress, study schedules, wants a learning plan, or asks what lesson to study next.\n\n"
            "Return the routing decision strictly as a JSON object matching this structure:\n"
            "{\n"
            "  \"agent\": \"tutor\" | \"quiz_generator\" | \"path_advisor\",\n"
            "  \"reason\": \"string explanation\"\n"
            "}"
        )
        
        # Render the recent messages as text context for the router
        history_lines = []
        for msg in messages[-5:]: # limit history context to recent 5 messages
            sender = "User" if isinstance(msg, HumanMessage) else "AI"
            history_lines.append(f"{sender}: {msg.content}")
        context_str = "\n".join(history_lines)
        
        response = await llm.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=f"Recent Conversation:\n{context_str}\n\nLast Query: {user_query}")],
            response_format={"type": "json_object"}
        )
        
        route_decision = json.loads(response.content)
        next_action = route_decision.get("agent", "tutor")
        
        logger.info(
            "orchestrator_route_success",
            selected_agent=next_action,
            reason=route_decision.get("reason")
        )
        return {
            "next_action": next_action,
            "current_agent": "orchestrator"
        }
        
    except Exception as e:
        logger.error("orchestrator_classification_failed", error=str(e))
        # Hard fallback to tutor in case of system failures
        return {
            "next_action": "tutor",
            "current_agent": "orchestrator",
            "error": f"Orchestrator failed to route: {str(e)}"
        }
