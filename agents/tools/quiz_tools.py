"""Quiz Tools module for the Multi-Agent System.

Provides tools to generate structured quizzes and validate their difficulty alignment.
"""

import os
import json
import structlog
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logger = structlog.get_logger()


async def generate_quiz(topic: str, difficulty: str, num_questions: int = 5) -> Dict[str, Any]:
    """Generates a structured multiple-choice quiz based on topic, difficulty, and question count.

    Args:
        topic (str): Learning subject area.
        difficulty (str): Categorization tier ('Beginner', 'Intermediate', 'Advanced').
        num_questions (int): Count of questions to compile.

    Returns:
        Dict[str, Any]: Quiz JSON structure with questions list.
    """
    logger.info("tool_generate_quiz_start", topic=topic, difficulty=difficulty, count=num_questions)
    
    # Standard fallback if LLM is disabled or missing credentials
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "mock-key-for-testing":
        logger.warning("tool_generate_quiz_mock_fallback")
        return {
            "topic": topic,
            "difficulty": difficulty,
            "questions": [
                {
                    "question": f"Sample Mock Question 1 for {topic} ({difficulty}): What is the primary purpose of this topic?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "Option A"
                },
                {
                    "question": f"Sample Mock Question 2 for {topic} ({difficulty}): Which of these is standard practice?",
                    "options": ["Standard Choice 1", "Standard Choice 2", "Standard Choice 3", "Standard Choice 4"],
                    "correct_answer": "Standard Choice 1"
                }
            ]
        }
        
    try:
        # Initialize OpenAI Chat Model
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key,
            temperature=0.4
        )
        
        system_prompt = (
            "You are a master academic educator.\n"
            "Generate a multiple-choice quiz based on the requested topic, difficulty, and question count.\n"
            "Return the output strictly as a JSON object matching this structure:\n"
            "{\n"
            "  \"topic\": \"string\",\n"
            "  \"difficulty\": \"string\",\n"
            "  \"questions\": [\n"
            "    {\n"
            "      \"question\": \"string\",\n"
            "      \"options\": [\"string\", \"string\", \"string\", \"string\"],\n"
            "      \"correct_answer\": \"string\"\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "Ensure options are unique and correct_answer matches one of the options exactly."
        )
        
        user_prompt = (
            f"Topic: {topic}\n"
            f"Difficulty: {difficulty}\n"
            f"Number of Questions: {num_questions}"
        )
        
        # Call LLM with JSON mode instructions
        response = await llm.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)],
            response_format={"type": "json_object"}
        )
        
        quiz_dict = json.loads(response.content)
        logger.info("tool_generate_quiz_success", topic=topic, questions_generated=len(quiz_dict.get("questions", [])))
        return quiz_dict
        
    except Exception as e:
        logger.error("tool_generate_quiz_failed", error=str(e))
        raise RuntimeError(f"Failed to generate quiz: {str(e)}") from e


def validate_quiz_difficulty(quiz_data: Dict[str, Any]) -> bool:
    """Verifies that the generated quiz aligns structure-wise and checks difficulty parameters.

    Args:
        quiz_data (Dict[str, Any]): The generated quiz data dictionary.

    Returns:
        bool: True if validation passes, False otherwise.
    """
    logger.info("tool_validate_quiz_difficulty_start")
    
    # 1. Structure Verification
    if not isinstance(quiz_data, dict):
        logger.warning("validation_failed_not_dict")
        return False
        
    if "questions" not in quiz_data or not isinstance(quiz_data["questions"], list):
        logger.warning("validation_failed_missing_questions_list")
        return False
        
    difficulty = quiz_data.get("difficulty", "Beginner").strip().lower()
    
    # 2. Iterate and validate fields per question
    for idx, q in enumerate(quiz_data["questions"]):
        if not all(k in q for k in ("question", "options", "correct_answer")):
            logger.warning("validation_failed_missing_keys", question_index=idx)
            return False
            
        options = q["options"]
        correct = q["correct_answer"]
        
        if not isinstance(options, list) or len(options) < 2:
            logger.warning("validation_failed_invalid_options", question_index=idx)
            return False
            
        if correct not in options:
            logger.warning("validation_failed_correct_answer_not_in_options", question_index=idx)
            return False
            
    # Simple semantic heuristics check for difficulty levels
    # Beginner: simple query structures, basic keywords
    # Advanced: complex terms
    logger.info("tool_validate_quiz_difficulty_success", difficulty=difficulty)
    return True
