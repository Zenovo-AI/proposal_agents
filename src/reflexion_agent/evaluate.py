"""
This module evaluates how similar a user's generated proposal is to previously retrieved examples.

- `compute_similarity`: Uses Python's `difflib` to calculate how similar two pieces of text are, returning a score between 0 and 1.
- `evaluate`: 
    - Compares the current proposal (`candidate`) with past examples (`examples`) stored in the state.
    - If the similarity is higher than a set threshold (95%), it marks the status as "success".
    - Otherwise, it marks the status as "retry", meaning the proposal should be revised.

This logic is useful in feedback loops where an AI agent refines its output by comparing it to known good examples.
"""



import difflib
from src.reflexion_agent.state import State

MAX_ITERATIONS = 3
SIMILARITY_THRESHOLD = 0.95  # How similar the proposals should be


def compute_similarity(text1: str, text2: str) -> float:
    return difflib.SequenceMatcher(None, text1.strip(), text2.strip()).ratio()


def evaluate(state: State) -> State:
    candidate_text = state["candidate"].content
    retrieved_text = state["examples"]

    similarity = compute_similarity(candidate_text, retrieved_text)
    print(f"[evaluate] Similarity Score: {similarity:.4f}")
    if similarity >= SIMILARITY_THRESHOLD:
        state["status"] = "success"
    else:
        state["status"] = "retry"

    return state

