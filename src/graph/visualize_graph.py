from IPython.display import Image, display
from src.rag_agent.inference import generate_draft
from src.reflexion_agent.critic import critic as wrapped_critic
from src.reflexion_agent.evaluate import evaluate
from src.reflexion_agent.retriever import retrieve_examples
from src.reflexion_agent.state import State
from src.graph.node_edges import create_state_graph


graph = create_state_graph(State, generate_draft, retrieve_examples, wrapped_critic, evaluate)

try:
    img_data = graph.get_graph().draw_mermaid_png()
    with open("graph_output.png", "wb") as f:
        f.write(img_data)
    print("Graph saved as graph_output.png")
except Exception:
    # This requires some extra dependencies and is optional
    pass


