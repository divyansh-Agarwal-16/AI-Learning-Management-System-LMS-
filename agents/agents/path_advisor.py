"""Path Advisor Agent module for the Multi-Agent System.

Uses progress and recommendation tools to compile a personalized 7-day learning path.
"""

import os
import structlog
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from agents.state import AgentState
from agents.tools.progress_tools import get_user_progress, recommend_next_lesson

logger = structlog.get_logger()


async def path_advisor_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Path advisor node that builds a 7-day study plan from student database stats.

    Args:
        state (AgentState): Unified graph state.
        config (RunnableConfig): Runtime config containing the database session.

    Returns:
        Dict[str, Any]: State updates with the study plan.
    """
    messages = state.get("messages", [])
    user_id = state.get("user_id")
    course_id = state.get("course_id")
    
    logger.info("path_advisor_node_entry", user_id=user_id, course_id=course_id)
    
    # Resolve the database session from runtime configurations
    db = config.get("configurable", {}).get("db")
    if not db:
        logger.error("path_advisor_missing_db")
        error_msg = "Database session is not available. Cannot fetch study progress."
        return {
            "messages": messages + [AIMessage(content=error_msg)],
            "next_action": "orchestrator",
            "current_agent": "path_advisor"
        }
        
    # 1. Fetch User Progress metrics
    progress = await get_user_progress(user_id=user_id, course_id=course_id, db=db)
    
    # 2. Fetch recommended next lesson details
    next_lesson = await recommend_next_lesson(user_id=user_id, course_id=course_id, db=db)
    
    # 3. Prompt construction for study plan generation
    rec_lesson_str = "None (Course is fully completed!)"
    if next_lesson:
        rec_lesson_str = (
            f"Title: {next_lesson.get('title')}\n"
            f"Order Index: {next_lesson.get('order')}\n"
            f"Estimated Duration: {next_lesson.get('duration')}"
        )
        
    progress_str = (
        f"Completed: {progress.get('completed_lessons')} of {progress.get('total_lessons')} lessons.\n"
        f"Completion Percentage: {progress.get('percentage')}%\n"
        f"Current course status: {progress.get('status')}"
    )
    
    system_prompt = (
        "You are a specialized Path Advisor agent.\n"
        "Your goal is to build a highly structured, personalized 7-day study plan for the student based on their progress "
        "and recommended next lesson details.\n"
        "Break down the study plan day-by-day (Day 1 to Day 7), including tasks, recommended durations, and study tips.\n"
        "Always maintain an encouraging, academic tone."
    )
    
    user_prompt = (
        f"Student Study Progress:\n"
        f"{progress_str}\n\n"
        f"Recommended Next Lesson:\n"
        f"{rec_lesson_str}\n\n"
        f"Please generate the 7-day study plan:"
    )
    
    # 4. Invoke LLM (or mock fallback)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "mock-key-for-testing":
        logger.warning("path_advisor_llm_mock_fallback")
        mock_plan = (
            f"📅 **Personalized 7-Day Study Plan**\n"
            f"Here is your study schedule based on your progress:\n"
            f"- {progress_str}\n\n"
            f"**Recommended focus lesson:** {next_lesson.get('title') if next_lesson else 'Review'}\n\n"
            f"**Day 1-2**: Review notes on previous lessons (30 mins/day).\n"
            f"**Day 3-4**: Focus on the next lesson: '{next_lesson.get('title') if next_lesson else 'Course Wrapup'}' (45 mins/day).\n"
            f"**Day 5**: Practice with quizzes and review incorrect answers (40 mins).\n"
            f"**Day 6-7**: Solve practical coding problems related to the topic (60 mins/day)."
        )
        study_plan_dict = {
            "progress_summary": progress,
            "next_lesson_recommendation": next_lesson,
            "plan_text": mock_plan
        }
        return {
            "messages": messages + [AIMessage(content=mock_plan)],
            "study_plan": study_plan_dict,
            "next_action": "orchestrator",
            "current_agent": "path_advisor"
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
        
        study_plan_dict = {
            "progress_summary": progress,
            "next_lesson_recommendation": next_lesson,
            "plan_text": response.content
        }
        
        logger.info("path_advisor_llm_success")
        return {
            "messages": messages + [response],
            "study_plan": study_plan_dict,
            "next_action": "orchestrator",
            "current_agent": "path_advisor"
        }
    except Exception as e:
        logger.error("path_advisor_failed", error=str(e))
        error_msg = f"Path Advisor is currently offline. Error details: {str(e)}"
        return {
            "messages": messages + [AIMessage(content=error_msg)],
            "next_action": "orchestrator",
            "current_agent": "path_advisor",
            "error": str(e)
        }
