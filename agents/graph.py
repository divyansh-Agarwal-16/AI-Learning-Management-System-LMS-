"""Graph Assembly module for the Multi-Agent System.

Assembles the StateGraph, wires conditional edges, and compiles the flow with memory checkpointers.
"""

import sys
import structlog
from pathlib import Path
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

# Configure sys.path for root directory imports
root_path = Path(__file__).parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from agents.state import AgentState
from agents.agents.orchestrator import orchestrator_node
from agents.agents.tutor import tutor_node
from agents.agents.quiz_generator import quiz_generator_node
from agents.agents.path_advisor import path_advisor_node

logger = structlog.get_logger()


def route_decision(state: AgentState) -> str:
    """Evaluates next_action flag to decide transition to specialized node or END.

    Args:
        state (AgentState): Unified graph state.

    Returns:
        str: Name of the next transition destination.
    """
    action = state.get("next_action", "tutor").strip().lower()
    
    logger.info("graph_route_decision", action=action)
    
    if action == "tutor":
        return "tutor"
    elif action == "quiz_generator":
        return "quiz_generator"
    elif action == "path_advisor":
        return "path_advisor"
    else:
        return END


def build_lms_agent_graph():
    """Assembles the StateGraph routing nodes and compiles it with memory savers.

    Returns:
        CompiledStateGraph: The compiled state graph.
    """
    logger.info("building_lms_agent_graph_start")
    
    # Initialize state graph with our TypedDict schema
    workflow = StateGraph(AgentState)
    
    # Register all four agent nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("tutor", tutor_node)
    workflow.add_node("quiz_generator", quiz_generator_node)
    workflow.add_node("path_advisor", path_advisor_node)
    
    # Set the entry point to orchestrator dispatcher
    workflow.set_entry_point("orchestrator")
    
    # Configure conditional routing edges from orchestrator to specialized nodes
    workflow.add_conditional_edges(
        "orchestrator",
        route_decision,
        {
            "tutor": "tutor",
            "quiz_generator": "quiz_generator",
            "path_advisor": "path_advisor",
            END: END
        }
    )
    
    # Configure loopbacks returning execution control back to the orchestrator dispatcher
    workflow.add_edge("tutor", "orchestrator")
    workflow.add_edge("quiz_generator", "orchestrator")
    workflow.add_edge("path_advisor", "orchestrator")
    
    # Compile graph with persistent memory savers for session tracking
    memory = InMemorySaver()
    compiled_graph = workflow.compile(checkpointer=memory)
    
    logger.info("building_lms_agent_graph_success")
    return compiled_graph


# Compile the global graph instance
graph = build_lms_agent_graph()

if __name__ == "__main__":
    print("Multi-Agent Graph successfully assembled.")
