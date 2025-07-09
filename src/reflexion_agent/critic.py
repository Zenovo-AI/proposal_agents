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


from reflexion_agent.state import State
from utils import prompt_template
from langchain_core.messages import AIMessage # type: ignore
from langchain_openai import ChatOpenAI # type: ignore
from langchain_core.prompts import ChatPromptTemplate # type: ignore




# def critic(state: dict, config: dict) -> dict:
#     if not state.get("candidate") or not state.get("examples"):
#         state["status"] = "missing_inputs_for_critique"
#         return state
    
#     llm = ChatOpenAI

#     prompt = ChatPromptTemplate.from_template(prompt_template())
#     candidate_text = state["candidate"]
#     retrieved_text = state["examples"]

#     filled_prompt = prompt.invoke({
#         "generated_proposal": candidate_text,
#         "retrieved_proposal": retrieved_text
#     })

#     response = llm.invoke(filled_prompt)
#     new_candidate = response.content or candidate_text

#     print("[critic] Critique Result Preview:", new_candidate[:500])

#     state["candidate"] = AIMessage(content=new_candidate)
#     state["messages"] = state.get("messages", []) + [AIMessage(content=new_candidate)]
#     return state


def critic(state: dict, config: dict) -> dict:
    candidate_msg = state.get("candidate")
    retrieved = state.get("examples")

    # 🚫 Early exit if missing inputs
    if not candidate_msg or not retrieved:
        state["status"] = "missing_inputs_for_critique"
        return state

    # Instantiate the LLM
    llm = ChatOpenAI(model="gpt-4o-2024-08-06", temperature=0)

    # Build the critique prompt
    prompt = ChatPromptTemplate.from_template(prompt_template())
    filled = prompt.invoke({
        "generated_proposal": candidate_msg.content,
        "retrieved_proposal": retrieved
    })

    # Run the model and extract new content
    response: AIMessage = llm.invoke(filled)
    new_content = response.content or candidate_msg.content

    print("[critic] Critique Result Preview:", new_content[:500])

    # Save the updated candidate and append to messages
    state["candidate"] = AIMessage(content=new_content)
    state.setdefault("messages", []).append(AIMessage(content=new_content))
    return state


def critic_with_counter(state: dict, config: dict) -> dict:
    # Run original critic logic
    new_state = critic(state, config)

    # Increment loop counter
    loops = new_state.get("critic_loops", 0) + 1
    new_state["critic_loops"] = loops
    return new_state
