from src.reflexion_agent.state import State
from langgraph.types import Command, interrupt
from langgraph.graph import END

# def human_node(state: State): 
#     """Human Intervention node - loops back to model unless input is done"""

#     print("\n [human_node] awaiting human feedback...")

#     proposal = state["messages"][-1].content

#     # Interrupt to get user feedback

#     user_feedback = interrupt(
#         {
#             "generated_proposal": proposal, 
#             "message": "Provide feedback or type 'done' to finish"
#         }
#     )

#     print(f"[human_node] Received human feedback: {user_feedback}")

#     # If user types "done", transition to END node
#     if user_feedback.lower() == "done": 
#         return Command(update={"human_feedback": state["human_feedback"] + ["Finalised"]}, goto=END)

#     # Otherwise, update feedback and return to model for re-generation
#     return Command(update={"human_feedback": state["human_feedback"] + [user_feedback]}, goto="generate_draft")

def human_node(state: State):
    """Human Intervention node - waits for feedback before proceeding"""
    print("\n[human_node] awaiting human feedback...")
    
    # Interrupt the graph execution to wait for human input
    return interrupt("Please provide feedback to continue...")