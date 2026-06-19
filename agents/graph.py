import os
from typing import Annotated, TypedDict, List
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

load_dotenv()

# Define state structure
class AgentState(TypedDict):
    messages: List[BaseMessage]
    current_topic: str
    quiz_generated: bool
    evaluation: str

# Define nodes/agents
def tutor_node(state: AgentState):
    """Personalized AI Tutor node that explains concepts."""
    messages = state["messages"]
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4-turbo")
    
    system_prompt = (
        "You are an empathetic, expert AI Tutor. Explain concepts thoroughly, "
        "checking for understanding. If the user is ready, route to quiz generation."
    )
    
    # Simple invoke (mock or LLM call if keys are set)
    if os.getenv("OPENAI_API_KEY"):
        response = llm.invoke([AIMessage(content=system_prompt)] + messages)
        new_messages = messages + [response]
    else:
        new_messages = messages + [AIMessage(content="[Tutor Agent] Let's learn about Python! Are you ready for a quiz?")]
        
    return {
        "messages": new_messages,
        "current_topic": state.get("current_topic", "General"),
        "quiz_generated": state.get("quiz_generated", False)
    }

def quiz_generator_node(state: AgentState):
    """Node that generates quiz questions based on the topic."""
    messages = state["messages"]
    
    quiz_msg = AIMessage(content="[Quiz Generator Agent] Here is your question: What is a lambda function in Python?")
    
    return {
        "messages": messages + [quiz_msg],
        "quiz_generated": True
    }

# Router condition
def should_continue(state: AgentState):
    """Determine whether to generate a quiz or stay in tutoring phase."""
    # Check if the user requested a quiz or if the tutor decided to quiz
    messages = state["messages"]
    last_message = messages[-1].content.lower() if messages else ""
    
    if "ready" in last_message or "quiz" in last_message:
        return "generate_quiz"
    return END

# Build the workflow graph
def build_lms_agent_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("tutor", tutor_node)
    workflow.add_node("quiz_generator", quiz_generator_node)
    
    # Set entry point
    workflow.set_entry_point("tutor")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "tutor",
        should_continue,
        {
            "generate_quiz": "quiz_generator",
            END: END
        }
    )
    
    # Add normal edges
    workflow.add_edge("quiz_generator", END)
    
    # Compile
    return workflow.compile()

if __name__ == "__main__":
    app_graph = build_lms_agent_graph()
    print("LangGraph Multi-Agent flow successfully compiled.")
