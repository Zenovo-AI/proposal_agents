from reflexion_agent.human_feedback import human_node
from rag_agent.inference import generate_draft
from reflexion_agent.critic import critic as wrapped_critic
from structure_agent.structureAgent import structure_node
from reflexion_agent.retriever import retrieve_examples
from reflexion_agent.state import State
from graph.node_edges import control_edge, create_state_graph


graph = create_state_graph(State, structure_node, generate_draft, retrieve_examples, wrapped_critic, human_node, control_edge)

try:
    img_data = graph.get_graph().draw_mermaid_png(max_retries=5, retry_delay=2.0)
    with open("graph_output.png", "wb") as f:
        f.write(img_data)
    print("Graph saved as graph_output.png")
except Exception as e:
    print(f"Failed to save graph image: {e}")

