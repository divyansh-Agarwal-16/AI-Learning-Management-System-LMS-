"""State Schema module for the LangGraph Multi-Agent System.

Defines the structure of the shared execution state passed between agent nodes.
"""

from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """The state schema for the multi-agent graph system.

    Attributes:
        messages (List[BaseMessage]): Accumulated chat history between user and agents.
        current_agent (str): Name of the active agent node (e.g. 'orchestrator', 'tutor', 'quiz_generator', 'path_advisor').
        user_id (str): UUID representation of the student requesting help.
        course_id (str): UUID representation of the course context.
        context (List[str]): List of parsed context text chunks retrieved from RAG.
        quiz_data (Optional[Dict[str, Any]]): Struct of generated quiz details (questions, answers, difficulty).
        study_plan (Optional[Dict[str, Any]]): Struct of generated 7-day personal schedule milestones.
        next_action (str): Control flag specifying the routing destination (e.g. 'tutor', 'orchestrator', 'end').
        error (Optional[str]): Error messages indicating processing faults.
    """
    messages: List[BaseMessage]
    current_agent: str
    user_id: str
    course_id: str
    context: List[str]
    quiz_data: Optional[Dict[str, Any]]
    study_plan: Optional[Dict[str, Any]]
    next_action: str
    error: Optional[str]
