from reflexion_agent.state import State


def end_node(state: State): 
    """ Final node """
    return {
        "proposal": state["messages"][-1].content,
        "human_feedback": state["human_feedback"][-1].content
    }
