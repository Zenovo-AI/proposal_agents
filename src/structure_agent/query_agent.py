import json
import logging
from openai import AsyncOpenAI # type: ignore
from fastapi import HTTPException # type: ignore
from utils import query_agent_prompt
from langchain_core.messages import AIMessage # type: ignore
from config.appconfig import settings as app_settings


# async def query_understanding_agent(state: dict, config: dict) -> dict:
#     user_query = state.get("user_query", "").strip()
#     if not user_query:
#         raise HTTPException(status_code=400, detail="Missing user_query in state")
    
#     System_prompt = query_agent_prompt()

#     client = AsyncOpenAI(api_key=app_settings.openai_api_key)
#     response = await client.chat.completions.create(
#         model="gpt-4-1106-preview",  # GPT‑4.1
#         messages=[
#             {"role": "system", "content": System_prompt},
#             {"role": "user", "content": user_query}
#         ],
#         temperature=0.0
#     )

#     raw = response.choices[0].message.content.strip()
#     logging.info(f"Raw response from query understanding agent: {raw}")
#     try:
#         result = json.loads(raw)
#     except json.JSONDecodeError:
#         # Fallback if model doesn't output valid JSON
#         state["messages"].append({"role":"assistant","content":
#             "Sorry, I couldn't parse the clarification result. Could you please rephrase?"})
#         state["needs_clarification"] = True
#         return state

#     if result.get("status") == "needs_clarification":
#         state["messages"].append({"role":"assistant","content": result["message"]})
#         state["needs_clarification"] = True
#     elif result.get("status") == "clarified":
#         state["user_query"] = result["clarified_query"]
#         state["clarified_query"] = result["clarified_query"]
#         state["needs_clarification"] = False
#     else:
#         state["messages"].append({"role":"assistant","content":
#             "Unexpected response. Could you please clarify your request?"})
#         state["needs_clarification"] = True

#     return state


async def query_understanding_agent(state: dict, config: dict) -> dict:
    user_query = state.get("user_query", "").strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Missing user_query in state")

    system_prompt = query_agent_prompt()  # define this prompt

    client = AsyncOpenAI(api_key=app_settings.openai_api_key)
    response = await client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        temperature=0.0
    )

    raw = response.choices[0].message.content.strip()
    logging.info("Raw response: %s", raw)
    if not raw:
        raise ValueError("query_understanding_agent got empty response from LLM")

    # Parse the JSON
    parsed = json.loads(raw)

    msg = parsed.get("message", "")
    state["messages"] = [AIMessage(content=msg)]
    state["needs_clarification"] = parsed.get("needs_clarification", False)
    
    logging.info(f"Raw response from query agent: {raw}")
    

    logging.info("State after query understanding: %s", state)


    return state

