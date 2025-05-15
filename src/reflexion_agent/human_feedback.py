"""
This module defines the human intervention node in the Reflexion Agent workflow.
It halts the graph execution at a designated point to await human feedback before proceeding,
enabling real-time review and control over automated reasoning steps.
"""

from src.reflexion_agent.state import State
from langgraph.types import Command, interrupt
from langgraph.graph import END



def human_node(state: State):
    """Human Intervention node - waits for feedback before proceeding"""
    print("\n[human_node] awaiting human feedback...")
    
    # Interrupt the graph execution to wait for human input
    return interrupt("Please provide feedback to continue...")