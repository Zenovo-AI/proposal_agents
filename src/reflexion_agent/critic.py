"""
This module defines the `critic` function, which improves a candidate proposal by critiquing it against previous examples.

- `critic(state, llm)`: 
    - Takes the current state and a language model (`llm`) as inputs.
    - Checks if both the candidate proposal and retrieved examples exist in the state.
    - If they are missing, it updates the state to indicate missing inputs.
    - If present, it fills a prompt using the candidate and example proposals.
    - The language model then critiques the candidate by comparing it with the examples.
    - The improved version of the candidate is saved back to the state along with a message log.

This is useful in reflexion loops where an LLM self-critiques and refines its own output using contextual examples.
"""


from src.reflexion_agent.state import State
from src.utils import prompt_template
from langchain_core.messages import AIMessage # type: ignore
from langchain_openai import ChatOpenAI # type: ignore
from langchain_core.prompts import ChatPromptTemplate # type: ignore



def critic(state: State, llm: ChatOpenAI) -> State:
    if not state.get("candidate") or not state.get("examples"):
        state["status"] = "missing_inputs_for_critique"
        return state

    prompt = ChatPromptTemplate.from_template(prompt_template())
    candidate_text = state["candidate"].content
    retrieved_text = state["examples"]

    filled_prompt = prompt.invoke({
        "generated_proposal": candidate_text,
        "retrieved_proposal": retrieved_text
    })

    response = llm.invoke(filled_prompt)
    new_candidate = response.content or candidate_text

    print("[critic] Critique Result Preview:", new_candidate[:500])

    state["candidate"] = AIMessage(content=new_candidate)
    state["messages"] = state.get("messages", []) + [AIMessage(content=new_candidate)]
    return state

