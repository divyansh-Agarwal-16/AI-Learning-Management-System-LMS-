"""Unit tests for the LangGraph Multi-Agent system.

Tests state graph compilation, central orchestrator routing, and helper tools.
"""

import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Configure paths to resolve local imports
root_path = Path(__file__).parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from langchain_core.messages import HumanMessage, AIMessage
from agents.state import AgentState
from agents.graph import graph, route_decision
from agents.agents.orchestrator import orchestrator_node
from agents.tools.quiz_tools import validate_quiz_difficulty


class TestAgentsSystem(unittest.IsolatedAsyncioTestCase):
    """Test suite validating the multi-agent orchestration and tools."""

    def test_graph_compilation(self):
        """Verifies that the LangGraph StateGraph compiles and registers all nodes."""
        self.assertIsNotNone(graph)
        node_names = graph.nodes.keys()
        self.assertIn("orchestrator", node_names)
        self.assertIn("tutor", node_names)
        self.assertIn("quiz_generator", node_names)
        self.assertIn("path_advisor", node_names)

    def test_routing_decisions(self):
        """Verifies conditional routing decisions map next_action fields accurately."""
        # Route to tutor
        state_tutor = {"next_action": "tutor"}
        self.assertEqual(route_decision(state_tutor), "tutor")

        # Route to quiz generator
        state_quiz = {"next_action": "quiz_generator"}
        self.assertEqual(route_decision(state_quiz), "quiz_generator")

        # Route to path advisor
        state_advisor = {"next_action": "path_advisor"}
        self.assertEqual(route_decision(state_advisor), "path_advisor")

        # Route to END
        state_end = {"next_action": "end"}
        self.assertEqual(route_decision(state_end), "__end__")

    async def test_orchestrator_concludes_turn_on_ai_response(self):
        """Ensures that orchestrator returns 'end' when the last message is from an AI agent."""
        state = {
            "messages": [HumanMessage(content="Explain python"), AIMessage(content="Python is...")],
            "current_agent": "tutor",
            "next_action": "orchestrator",
            "user_id": "1",
            "course_id": "1",
            "context": [],
            "quiz_data": None,
            "study_plan": None,
            "error": None
        }
        res = await orchestrator_node(state)
        self.assertEqual(res["next_action"], "end")

    @patch("agents.agents.orchestrator.ChatOpenAI")
    async def test_orchestrator_routing_heuristics_fallback(self, mock_llm):
        """Verifies fallback classification heuristics route queries correctly when key is unset."""
        # Temporarily clear OpenAI API key from env to test fallback
        with patch.dict("os.environ", {}, clear=True):
            # 1. Tutor request
            state_tutor = {"messages": [HumanMessage(content="Explain loops")]}
            res_tutor = await orchestrator_node(state_tutor)
            self.assertEqual(res_tutor["next_action"], "tutor")

            # 2. Quiz request
            state_quiz = {"messages": [HumanMessage(content="Can you give me a quiz?")]}
            res_quiz = await orchestrator_node(state_quiz)
            self.assertEqual(res_quiz["next_action"], "quiz_generator")

            # 3. Path Advisor request
            state_path = {"messages": [HumanMessage(content="What is my progress?")]}
            res_path = await orchestrator_node(state_path)
            self.assertEqual(res_path["next_action"], "path_advisor")

    def test_quiz_difficulty_validation(self):
        """Verifies structural correctness and difficulty keys validation of quizzes."""
        # Valid quiz data
        valid_quiz = {
            "topic": "Python OOP",
            "difficulty": "Beginner",
            "questions": [
                {
                    "question": "What is self in Python?",
                    "options": ["Instance reference", "Class reference", "Global name", "None"],
                    "correct_answer": "Instance reference"
                }
            ]
        }
        self.assertTrue(validate_quiz_difficulty(valid_quiz))

        # Invalid quiz data (missing correct answer in options)
        invalid_quiz = {
            "topic": "Python OOP",
            "difficulty": "Beginner",
            "questions": [
                {
                    "question": "What is self?",
                    "options": ["A", "B"],
                    "correct_answer": "C"
                }
            ]
        }
        self.assertFalse(validate_quiz_difficulty(invalid_quiz))


if __name__ == "__main__":
    unittest.main()
