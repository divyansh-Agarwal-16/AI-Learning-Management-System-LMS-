"""Quiz Generator Agent module for the Multi-Agent System.

Uses LLM tools to create topic quizzes and applies human-in-the-loop validation checkpoints.
"""

import os
import json
import structlog
from typing import Dict, Any
from langgraph.errors import NodeInterrupt
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agents.state import AgentState
from agents.tools.quiz_tools import generate_quiz, validate_quiz_difficulty

logger = structlog.get_logger()


async def quiz_generator_node(state: AgentState) -> Dict[str, Any]:
    """Generates MCQs and pauses execution with NodeInterrupt for review validation.

    Args:
        state (AgentState): Unified graph state.

    Returns:
        Dict[str, Any]: State updates with quiz JSON data.
    """
    messages = state.get("messages", [])
    quiz_data = state.get("quiz_data")
    
    logger.info("quiz_generator_node_entry", has_quiz_data=quiz_data is not None, message_count=len(messages))
    
    # 1. Human-in-the-Loop Resumption Check:
    # If quiz_data exists, it means the graph was interrupted previously to await approval.
    if quiz_data:
        last_message = messages[-1].content.lower().strip() if messages else ""
        logger.info("quiz_generator_review_check", user_response=last_message)
        
        # Check if approved
        if last_message in ("approve", "yes", "looks good", "y", "ok"):
            logger.info("quiz_generator_review_approved")
            
            # Format quiz questions as a readable text message to return to the user
            formatted_quiz = (
                f"📝 **Quiz Approved! Here are your questions:**\n\n"
                f"**Topic:** {quiz_data.get('topic')}\n"
                f"**Difficulty:** {quiz_data.get('difficulty')}\n\n"
            )
            for idx, q in enumerate(quiz_data.get("questions", [])):
                formatted_quiz += f"{idx + 1}. {q.get('question')}\n"
                for opt in q.get("options", []):
                    formatted_quiz += f"   - {opt}\n"
                formatted_quiz += "\n"
                
            formatted_quiz += "Reply with your answers when you are ready!"
            
            return {
                "messages": messages + [AIMessage(content=formatted_quiz)],
                "next_action": "orchestrator",
                "current_agent": "quiz_generator"
                # Keep quiz_data in state so it remains available in history
            }
        elif last_message in ("no", "regenerate", "reject", "change"):
            logger.info("quiz_generator_review_rejected")
            # Clear current quiz and fall through to generate a new one
            quiz_data = None
        else:
            # User sent something else, request review decision explicitly
            logger.info("quiz_generator_review_waiting")
            raise NodeInterrupt(
                "A quiz has been generated and is awaiting your approval. "
                "Please respond with 'approve' to send it to the student, or 'regenerate' to recreate it."
            )

    # 2. Base Generation Phase:
    # Find the topic and difficulty from recent history
    user_query = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_query = msg.content
            break
            
    # Classify topic and difficulty
    topic = "Python Programming"
    if "data" in user_query.lower() or "pandas" in user_query.lower():
        topic = "Data Science"
    elif "agent" in user_query.lower() or "langgraph" in user_query.lower():
        topic = "LangGraph Multi-Agents"
    elif "rag" in user_query.lower() or "llama" in user_query.lower():
        topic = "LlamaIndex RAG"
        
    difficulty = "Beginner"
    if "hard" in user_query.lower() or "advanced" in user_query.lower():
        difficulty = "Advanced"
    elif "medium" in user_query.lower() or "intermediate" in user_query.lower():
        difficulty = "Intermediate"
        
    logger.info("quiz_generator_generating", topic=topic, difficulty=difficulty)
    
    # Generate the quiz questions list
    try:
        new_quiz = await generate_quiz(topic=topic, difficulty=difficulty, num_questions=3)
        
        # Validate difficulty structure
        is_valid = validate_quiz_difficulty(new_quiz)
        if not is_valid:
            logger.warning("quiz_generator_validation_failed")
            # fallback adjustments
            new_quiz["difficulty"] = difficulty
            
        logger.info("quiz_generator_triggering_interrupt")
        
        # Store in state and raise NodeInterrupt to trigger the checkpoint approval
        # In a real environment, the admin/teacher reviews this JSON in their dashboard
        state["quiz_data"] = new_quiz
        
        # Append details for reviewer visibility before raising the interrupt
        review_notice = (
            f"[SYSTEM REVIEW CHANNELS - QUIZ PENDING APPROVAL]\n"
            f"Topic: {new_quiz.get('topic')}\n"
            f"Difficulty: {new_quiz.get('difficulty')}\n"
            f"Questions compiled: {len(new_quiz.get('questions', []))}\n\n"
            "Instructors: Please review and reply with 'approve' or 'regenerate'."
        )
        
        # We save state modifications before interrupting
        # In LangGraph, when NodeInterrupt is raised, the state changes returned are discarded,
        # but modifications to mutable state objects like dict keys in the state argument are captured,
        # or we can raise NodeInterrupt carrying the message.
        # To ensure the quiz_data is persisted, we must set it in state.
        # We raise NodeInterrupt containing the review notification text.
        raise NodeInterrupt(review_notice)
        
    except NodeInterrupt:
        # Re-raise NodeInterrupt to let LangGraph capture the pause
        raise
    except Exception as e:
        logger.error("quiz_generator_failed", error=str(e))
        error_msg = f"Failed to generate quiz: {str(e)}"
        return {
            "messages": messages + [AIMessage(content=error_msg)],
            "next_action": "orchestrator",
            "current_agent": "quiz_generator",
            "error": str(e)
        }
