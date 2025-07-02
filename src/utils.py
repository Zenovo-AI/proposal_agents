"""
Text processing functions for cleaning and formatting content.

- `unbold_text`: Converts bold characters (numbers and letters) to regular form.
- `unitalic_text`: Converts italic characters (letters) to regular form.
- `remove_emojis_and_symbols`: Removes emojis and specific symbols from the text.
- `replace_urls_with_placeholder`: Replaces URLs in the text with a placeholder.
- `remove_non_ascii`: Removes non-ASCII characters from the text.
- `clean_text`: Combines all cleaning functions to process and clean text content.
- `format_response`: Splits and formats chatbot responses into readable sentences.
"""

import ast
import json
import logging
import re
from typing import List
from datamodel import ProposalStructure
from intent_router.intent_router import detect_intent
from structure_agent.defined_proposal_strucutre import proposal_structure
from langchain_core.documents import Document # type: ignore
from unstructured.cleaners.core import (clean, clean_non_ascii_chars, replace_unicode_quotes) # type: ignore
from langchain_openai import OpenAI # type: ignore
from config.appconfig import settings as app_settings
from langchain_core.messages import AIMessage # type: ignore

proposal_structure_json = json.dumps(proposal_structure(), indent=2)


def unbold_text(text):
    # Mapping of bold numbers to their regular equivalents
    bold_numbers = {
        "𝟬": "0",
        "𝟭": "1",
        "𝟮": "2",
        "𝟯": "3",
        "𝟰": "4",
        "𝟱": "5",
        "𝟲": "6",
        "𝟳": "7",
        "𝟴": "8",
        "𝟵": "9",
    }

    # Function to convert bold characters (letters and numbers)
    def convert_bold_char(match):
        char = match.group(0)
        # Convert bold numbers
        if char in bold_numbers:
            return bold_numbers[char]
        # Convert bold uppercase letters
        elif "\U0001d5d4" <= char <= "\U0001d5ed":
            return chr(ord(char) - 0x1D5D4 + ord("A"))
        # Convert bold lowercase letters
        elif "\U0001d5ee" <= char <= "\U0001d607":
            return chr(ord(char) - 0x1D5EE + ord("a"))
        else:
            return char  # Return the character unchanged if it's not a bold number or letter

    # Regex for bold characters (numbers, uppercase, and lowercase letters)
    bold_pattern = re.compile(
        r"[\U0001D5D4-\U0001D5ED\U0001D5EE-\U0001D607\U0001D7CE-\U0001D7FF]"
    )
    text = bold_pattern.sub(convert_bold_char, text)

    return text


def unitalic_text(text):
    # Function to convert italic characters (both letters)
    def convert_italic_char(match):
        char = match.group(0)
        # Unicode ranges for italic characters
        if "\U0001d608" <= char <= "\U0001d621":  # Italic uppercase A-Z
            return chr(ord(char) - 0x1D608 + ord("A"))
        elif "\U0001d622" <= char <= "\U0001d63b":  # Italic lowercase a-z
            return chr(ord(char) - 0x1D622 + ord("a"))
        else:
            return char  # Return the character unchanged if it's not an italic letter

    # Regex for italic characters (uppercase and lowercase letters)
    italic_pattern = re.compile(r"[\U0001D608-\U0001D621\U0001D622-\U0001D63B]")
    text = italic_pattern.sub(convert_italic_char, text)

    return text


def remove_emojis_and_symbols(text):
    # Extended pattern to include specific symbols like ↓ (U+2193) or ↳ (U+21B3)
    emoji_and_symbol_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"  # emoticons
        "\U0001f300-\U0001f5ff"  # symbols & pictographs
        "\U0001f680-\U0001f6ff"  # transport & map symbols
        "\U0001f1e0-\U0001f1ff"  # flags (iOS)
        "\U00002193"  # downwards arrow
        "\U000021b3"  # downwards arrow with tip rightwards
        "\U00002192"  # rightwards arrow
        "]+",
        flags=re.UNICODE,
    )

    return emoji_and_symbol_pattern.sub(r" ", text)


def replace_urls_with_placeholder(text, placeholder="[URL]"):
    # Regular expression pattern for matching URLs
    url_pattern = r"https?://\S+|www\.\S+"

    return re.sub(url_pattern, placeholder, text)


def remove_non_ascii(text: str) -> str:
    text = text.encode("ascii", "ignore").decode("ascii")
    return text


def clean_text(text_content: str) -> str:
    cleaned_text = unbold_text(text_content)
    cleaned_text = unitalic_text(cleaned_text)
    cleaned_text = remove_emojis_and_symbols(cleaned_text)
    cleaned_text = clean(cleaned_text)
    cleaned_text = replace_unicode_quotes(cleaned_text)
    cleaned_text = clean_non_ascii_chars(cleaned_text)
    cleaned_text = replace_urls_with_placeholder(cleaned_text)

    return cleaned_text

def query_agent_prompt(user_query) -> str:
    return """
    You are a Query Clarification and Routing Assistant for CDGA RAG SYSTEM and you are powered by GPT‑4.1.
    You are a deep thinker, Your decision is very important so you need to take your time to understand {user_query}
    You already have a knowledge base that the user want's to access by sending in the query. 
    Do not ask for the user to present a knowlegde base, just know that the question is clear. But if it is not, then ask for clarification.

    Your task:
    1. Analyze the user's input.
    2. If it's ambiguous, incomplete, or lacks details, **ask exactly one concise follow-up question** aimed at clarifying intent.
    Output JSON:
    {
        "needs_clarification": "True",
        "message": "<your clarifying question>"
        
    }
    *Do not* include any other keys or information.
    E.g: 
    - Write a proposal for drilling a compliant borehole to IMS standards
    - Write a proposal against section202
    
    3. If the query is sufficiently clear and self-contained, **rewrite it** as a fully detailed, actionable query.
    Decide if it can be handled directly by an LLM ("direct") or if it requires retrieval of external documents ("rag").
    Output JSON:
    {
        "needs_clarification": "False",
        "clarified_query": "<complete refined query>",
    }

    E.g:
    - Please draft a technical proposal for drilling a compliant borehole for seismic monitoring, following IMS requirements.
    - Could you outline the key steps and considerations for preparing a borehole drilling proposal that meets IMS standards for environmental monitoring?

    
    Rules:
    - Don’t answer or perform the user’s request—only clarify or refine.
    - Ask only one clarification at a time.
    - Keep tone polite, brief, and focused.
    - Output must be valid JSON and nothing else.
    - STRICTLY RETURN A VALID JSON FILE
    - Never ask for clarification when {user_query} is clarified!

    **STRICT RULES:**
    - Only output pure JSON—no code fences, markdown, or extra keys.
    - Don’t answer or perform the query—only clarify or refine.
    - Output must always be valid JSON.

    ### 🚫 Bad Example (malformed JSON output—do NOT copy this):

    ```json
    {
        "needs_clarification": "False",
        "clarified_query": "Provide a summary of CDGA's engineering design experience in borehole rehabilitation."
    }```
    """


def sanitize_email(email: str) -> str:
    """
    Convert an email address into a safe PostgreSQL identifier string.
    Replaces '@' and '.' with underscores and removes other invalid characters.
    """
    # Lowercase for consistency
    sanitized = email.lower()
    
    # Replace '@' and '.' with underscores
    sanitized = sanitized.replace('@', '_').replace('.', '_')
    
    # Remove any characters that are not letters, numbers, or underscores
    sanitized = re.sub(r'[^a-z0-9_]', '', sanitized)
    
    # Ensure it doesn't start with a number (PostgreSQL identifiers can't start with digits)
    if sanitized[0].isdigit():
        sanitized = 'u_' + sanitized
    
    return sanitized


def format_response(response):
    """
    Split response text into readable sentences and format for display.
    """
    sentences = re.split(r'(?<=[.!?])\s+', response)
    return '\n'.join(sentences)

def format_response(response):
    """Format the chatbot response for better readability."""
    sentences = re.split(r'(?<=[.!?])\s+', response)
    formatted_response = '\n'.join(sentences)
    return formatted_response

def parse_response_for_doc_ids(response):
    """
    Extracts doc_ids which can be filenames (e.g., mydoc.pdf) or URLs (e.g., https://...).
    """
    if isinstance(response, str):
        # Match URLs or any string that looks like a filename (e.g. with .pdf, .docx, etc.)
        urls = re.findall(r"https?://\S+", response)
        files = re.findall(r"\b[\w\-]+(?:\.\w{2,5})\b", response)  # matches file-like strings
        return list(set(urls + files))  # deduplicate
    return []



# def generate_explicit_query(query: str, structure: ProposalStructure) -> str:
#     """Expands the user query using the structure and merges it into a single, explicit query."""
#     llm = OpenAI(temperature=0, openai_api_key=app_settings.openai_api_key)

#     # 🛠️ Parse structure if it's an AIMessage
#     if isinstance(structure, AIMessage):
#         try:
#             structure = ast.literal_eval(structure.content)
#         except Exception as e:
#             print("[generate_explicit_query] Failed to parse structure.content:", structure.content)
#             raise ValueError("Invalid format for structure.content") from e

#     structure_type = structure["type"]
#     sections = structure.get("sections", [])
#     subsections = structure.get("subsections", [])
#     lots = structure.get("lot_titles", [])
#     attachments_required = structure.get("attachments", False)

#     # Format structure parts
#     section_list = "\n".join([f"- {s}" for s in sections]) if sections else "N/A"
#     subsection_list = "\n".join([f"- {s}" for s in subsections]) if subsections else "N/A"
#     lot_list = "\n".join([f"- {l}" for l in lots]) if lots else "None"

#     prompt = f"""
#     You are a proposal planning assistant. Your goal is to transform the vague user query into an **explicit, detailed set of instructions** for writing a technical proposal.
    
#     <context>
#     Understand the user **intent** before breaking down the queries.
#     - If the query is factual (e.g., "Who are CDGA’s primary international clients?" or "Can you write an Executive summary for what is requested on the RFQ?"),
#     break it down accordingly for a structured factual response.
#     - If the query is about generating a proposal (e.g., "Can you generate a proposal for a power infrastructure project in East Africa?"),
#     break it down strictly using the following structure: {proposal_structure_json}
#     </context>

#     Original user query:  
#     "{query}"

#     Identified Structure:
#     - Type: {structure_type}
#     - Sections:\n{section_list}
#     - Subsections:\n{subsection_list}
#     - LOT Titles:\n{lot_list}
#     - Attachments Required: {"Yes" if attachments_required else "No"}

#     Your job is to:
#     1. Break the query down into 20 detailed subqueries that reflect the above structure.
#     2. Connect each subsection to it's particular section
#     3. c
#     4. Finish with a "**Final Explicit Query**" combining all subqueries into one single request prompt that a proposal LLM can respond to.


#     Format:
#     **Expanded Queries:**
#     1. ...
#     2. ...
#     ...
#     8. ...

#     **Final Explicit Query:**
#     "... <single, comprehensive prompt here> ..."
#     """
#     response = llm.invoke(prompt)
#     return response.strip()


def generate_explicit_query(query: str, structure: ProposalStructure) -> str:
    """Expands the user query using the structure and merges it into a single, explicit query."""
    llm = OpenAI(temperature=0, openai_api_key=app_settings.openai_api_key)

    # 🛠️ Parse structure if it's an AIMessage
    if isinstance(structure, AIMessage):
        try:
            structure = ast.literal_eval(structure.content)
        except Exception as e:
            print("[generate_explicit_query] Failed to parse structure.content:", structure.content)
            raise ValueError("Invalid format for structure.content") from e

    structure_type = structure.get("type", "proposal")
    sections = structure.get("sections", [])
    subsections = structure.get("subsections", [])
    lots = structure.get("lot_titles", [])
    attachments_required = structure.get("attachments", False)

    # Format structure parts
    section_list = "\n".join([f"- {s}" for s in sections]) if sections else "N/A"
    subsection_list = "\n".join([f"- {s}" for s in subsections]) if subsections else "N/A"
    lot_list = "\n".join([f"- {l}" for l in lots]) if lots else "None"

    prompt = f"""
    You are a proposal planning assistant.

    Your task is to transform the vague or general user query into a **structured, detailed, and explicit prompt** to guide a proposal-writing language model. The final output must include 20 expanded sub-queries and then synthesize them into a single all-inclusive prompt called the **Final Explicit Query**.

    <context>
    Understand the user's **intent** (e.g., proposal generation, executive summary, or factual analysis).
    If the intent is to generate a proposal, expand it using the structure below. Otherwise, adapt it accordingly for a structured factual output.

    Use the provided structure dynamically:

    - Type: {structure_type}
    - Sections:
    {section_list}
    - Subsections:
    {subsection_list}
    - LOT Titles:
    {lot_list}
    - Attachments Required: {"Yes" if attachments_required else "No"}

    Also use these guiding principles:
    1. Incorporate specific procurement metadata (titles, deadlines, reference numbers, responsible contacts, submission rules).
    2. Extract scope of work and separate LOTs distinctly.
    3. Include contractor responsibilities, materials, and equipment.
    4. Specify reporting obligations and test procedures.
    5. Emphasize compliance with legal, safety, and country-specific standards.
    6. Account for quotation currency, taxes, insurance, invoicing, and payment terms.
    7. Identify required attachments and forms (e.g. Bidder’s Statement, Compliance Matrix).
    8. Highlight evaluation criteria and relevant contractual terms.
    9. Include key personnel on the project and their CVs
    9. Format everything in a structured query-to-prompt style.

    </context>

    Original user query:
    "{query}"

    ---

    Expanded Queries:
    1. …
    2. …
    … up to 20.

    Final Explicit Query:
    "…"
    """

    
    # print("[generate_explicit_query] Prompt sent to LLM:\n", prompt)

    try:
        response = llm.invoke(prompt)
        # print("[generate_explicit_query] Raw LLM response:\n", repr(response))
    except Exception as e:
        print("[generate_explicit_query] Exception during LLM call:", str(e))
        return ""
    return response.strip()



def proposal_prompt(user_query: str, retrieved_docs: list[Document]) -> str:
    query_intent = detect_intent(user_query)

    doc_section = f"""
    Use retrieved documents {retrieved_docs} as style examples (mirroring their phrasing and technical depth), and cite sources inline like “[Doc A]”.
    Only write a proposal using the format on the retrieved documents when the user's intent is 'full_proposal'.
    Do not include or reference the retrieved documents when the user's intent is 'simple_answer'.
    """ if query_intent == "full_proposal" else ""

    return f"""
    User Query:
    {user_query}

    You are CDGA‑AI, an expert proposal writer who can also answer factual questions for the Centre for Development of Green Alternatives (CDGA), an Irish technical consultancy established in 1998 with global experience in engineering design, consultancy, and training.

    The user's intent is: **{query_intent}**

    If the intent is 'simple_answer', respond clearly using the knowledge retrieved from the knowledge base and make sure your response is related to the {user_query}.  
    If the intent is 'full_proposal', generate a structured proposal using the style and structure of the provided retrieved documents.

    # CO‑STAR Instructions

    Context:
    You have access to retrieved documents detailing a client RFQ and CDGA’s capabilities.

    Objective:
    Generate a full technical proposal in response to the user's request — but only if the query intent is 'full_proposal'.

    Style:
    Professional, well‑structured, with clear headings and bullet points.

    Tone:
    Confident, respectful, and client‑focused.

    Audience:
    Technical evaluation team at an international organization (e.g., CTBTO).

    {doc_section}

    # Additional Instructions

    You are tasked with preparing formal proposals, bids, and technical responses for international engineering and development projects.

    <context>
    When a user asks a question, take your time to understand the intent before writing a response.
    Do not generate a proposal when the intent of the user is 'simple_answer'.
    In that case, provide only a clear and accurate answer to the question.

    If the intent is 'full_proposal', then:
    - Use the information available to you, especially the retrieved documents.
    - Do not include the RFQ No (CTBTO RFQ No. 2024-0108).
    - Write on behalf of CDGA with specific, context-rich, and professional responses.
    - Avoid generic language. Be precise, relevant, and cite sources like “[Doc A]”.
    - Always end proposals with a conclusion.
    - Always include credible CVs as part of the proposal.

    What does it mean to “write on behalf of CDGA”?

    **Example (bad):**
    "We can help with this project by applying general engineering principles."

    **Example (good):**
    "CDGA will leverage its established expertise in sustainable civil infrastructure to design and implement resilient water systems, 
    building on its prior success delivering projects across Sub-Saharan Africa in collaboration with UNDP and the African Union."

    </context>

    Your task is to generate a response based on:
    - The user’s query
    - The intent type: **{query_intent}**
    - (If proposal) The retrieved documents and structure provided

    ---Response Rules---
    - NO PREAMBLE
    - If intent is 'simple_answer': provide only the factual response with no proposal structure.
    - If intent is 'full_proposal':
        - Structure the document using clear headings and bullet points.
        - Cite the document sources when using specific facts or data.
        - Use this format exactly:
            Section Title

            [Then begin the paragraph content...]
        - Do NOT write section title and content on the same line.
        - Do NOT prefix section titles with symbols.
        - Include bullet points or numbered lists when helpful.
        - Use domain-relevant and technically accurate language.
        - Include credible CVs.

    Write clearly and professionally, as if the response will be reviewed by a technical evaluation committee.
    """



# def proposal_prompt(user_query: str, retrieved_docs: list[Document]) -> str:
#     query_intent = detect_intent(user_query)

#     doc_section = f"""
#     Use retrieved documents {retrieved_docs} as style examples (mirroring their phrasing and technical depth), and cite sources inline like “[Doc A]”.
#     Only write a proposal using the format on the retrieved documents when the user's intent is 'full_proposal'.
#     Do not include or reference the retrieved documents when the user's intent is 'simple_answer'.
#     """ if query_intent == "full_proposal" else ""

#     return f"""
#     User Query:
#     {user_query}


#     You are CDGA‑AI, an expert proposal writer who can also answer factual answer for Centre for Development of Green Alternatives (CDGA), an Irish technical consultancy established in 1998 with global experience in engineering design, consultancy, and training. 
    
#     The user's intent is: **{query_intent}**

#     If the intent is 'simple_answer', respond clearly and concisely without using any proposal format or retrieved documents.  
#     If the intent is 'full_proposal', generate a structured proposal using the style and structure of the provided retrieved documents.

#     # CO‑STAR Instructions

#     Context:
#     You have access to retrieved documents detailing a client RFQ and CDGA’s capabilities.

#     Objective:
#     Generate a full technical proposal in response to the user's request.

#     Style:
#     Professional, well‑structured, with clear headings and bullet points.

#     Tone:
#     Confident, respectful, and client‑focused.

#     Audience:
#     Technical evaluation team at an international organization (e.g., CTBTO).

#     Use retrieved documents {retrieved_docs} as style examples (mirroring their phrasing and technical depth), and cite sources inline like “[Doc A]”.
#     Even though you are mirrioring the {retrieved_docs} still have it in mind not to write a proposal, when the user's intent {query_intent} is a simple or factual answer.
#     Only write a proposal using the format on {retrieved_docs} when you understand the user's intent {query_intent} to be proposal, else just answer the question asked by the user.

#     # Additional Instructions
        

#     You are tasked with preparing formal proposals, bids, and technical responses for international engineering and development projects.

#     <context>
#     When a user asks a question, take your time to understand the intent before writing a response.
#     Ensure you have all the necessary information to provide a comprehensive answer.
#     You are provided with a knowledge base that contains information about the organization, its capabilities, and the specific project requirements.
#     The user may ask for a proposal, bid, or project plan, and you need to respond accordingly.
#     Do not write a proposal when the intent of the user is to retrieve a simple answer — that is why it is important that you understand the **intent of the user**.
#     Remember to use the information available to you. Do not include proposal structure elements when answering factual questions.
#     Avoid generic or templated responses — be specific, as in a real RFP breakdown.
#     Do not generate a proposal when the intent of the user is 'simple_answer', In that case, provide only a clear and accurate answer to the question.

#     Your role is to respond thoughtfully and professionally, based on a deep understanding of both the user’s intent and the context provided. 
#     You are equipped with a knowledge base that includes details about CDGA’s organizational capabilities, past performance, project methodologies, and relevant technical frameworks.

#     Always assess whether the user is requesting a detailed proposal, a project plan, or simply asking a factual question. 
#     **Do not generate a proposal when the user's intent is only to retrieve information** — focus on clarity and relevance.

#     If the request clearly requires a formal proposal, generate a structured, well-developed, and technically sound response that speaks **on behalf of CDGA**.

#     What does it mean to “write on behalf of CDGA”?

#     **Example (bad):**
#     "We can help with this project by applying general engineering principles."

#     **Example (good):**
#     "CDGA will leverage its established expertise in sustainable civil infrastructure to design and implement resilient water systems, 
#     building on its prior success delivering projects across Sub-Saharan Africa in collaboration with UNDP and the African Union."

#     Focus on accuracy, professionalism, and completeness. Always end every proposal with a conclusion. No preambles.
#     </context>


#     Your task is to generate a complete, highly comprehensive technical proposal based on:
#     - The user’s request
#     - The expanded query provided
#     - The predefined structure including type, sections, subsections, and LOT titles

#     ---Response Rules---
#     - Structure the document using clear headings and bullet points.
#     - Cite the document sources when using specific facts or data.

#     Guidelines:
#     - Start each section on a new line with the section title clearly separated from the content.
#     - Use this format exactly:
#         Section Title
#         [followed by a blank line]
#         [Then begin the paragraph content...]
#     - Do NOT write the section title and content on the same line.
#     - Do NOT prefix section titles with punctuation (e.g., ":", "-", or "#").
#     - Follow the structure exactly as defined in the input.
#     - Use informative, well-developed paragraphs and include bullet points or numbered lists where helpful.
#     - Do not include greetings or closing remarks unless explicitly required.
#     - Use real-world detail and domain knowledge appropriate for organizations like CTBTO or UNDP.
#     - Incorporate feedback if provided.
#     - Always add credible CV's when writing a proposal

#     Write clearly and professionally, as if this proposal will be submitted directly to a technical evaluation committee.
#     """


def prompt_template():
    return """
    You are an expert in reviewing proposals. You have two documents to analyze:

    1. **Generated Proposal**: This is the proposal that has been generated by the system. It is in its draft form.
    2. **Retrieved Proposal**: This is an existing proposal that represents the correct format, structure, and content you are aiming for.

    Your task is to compare the **Generated Proposal** with the **Retrieved Proposal**. Please do the following:

    1. Point out the differences between the two proposals.
    2. Identify any missing or underdeveloped sections in the **Generated Proposal** that are present in the **Retrieved Proposal**.
    3. Suggest specific changes to the **Generated Proposal** to make it more aligned with the **Retrieved Proposal**. These changes should include improvements in structure, content, language, and any other relevant details.
    4. If there are any inconsistencies, clarify them and suggest how the **Generated Proposal** can be modified to address these inconsistencies.

    Return your feedback and the revised **Generated Proposal** in the same format as the **Generated Proposal**.

    **Generated Proposal:**
    {{candidate}}

    **Retrieved Proposal:**
    {{examples_str}}

    ---

    Please provide a detailed critique of the **Generated Proposal** based on the **Retrieved Proposal**.
    """

def sql_expert_prompt() -> str:
    """
    Returns a detailed system prompt to instruct an LLM to act as an expert SQL agent
    for RFQ search and retrieval from a PostgreSQL database.
    """
    return """
    You are a highly skilled SQL analyst and data engineer tasked with helping users search a structured relational database of Request for Quotation (RFQ) documents.

    Your role is mission-critical: the SQL queries you generate are directly used to retrieve important government and commercial RFQs that influence funding, project timelines, and strategic decisions.

    Please follow these principles:

    1. **Expertise**: Write fluent, optimized SQL for PostgreSQL.
    2. **Precision**: The accuracy of your query is vital. Do not assume column names—only use columns that are documented or provided.
    3. **Security**: Never write queries that could expose the system to SQL injection or data leakage. All inputs are sanitized.
    4. **Relevance**: Focus queries on retrieving useful, meaningful results. Prioritize fields like:
    - reference_no
    - title
    - submission_deadline
    - country_or_region
    - organization_name
    - document_name or file_name
    5. **Clarity**: Structure the query clearly, using aliases, ordering, and filtering where needed.
    6. **User Intent**: Interpret the user's natural language query with precision, identifying keywords and mapping them to relevant fields.
    7. **Fail-Safe**: If you are unsure of the schema, return a clarifying message or fallback query with minimal risk.

    You are not generating dummy or illustrative queries — your SQL will be executed directly against live data. Accuracy and safety are non-negotiable.

    Example User Input:
    “Show me all RFQs from Nigeria that are still open and mention solar energy.”

    Expected SQL Output:
    SELECT reference_no, title, submission_deadline, country_or_region
    FROM rfqs
    WHERE country_or_region ILIKE '%Nigeria%'
    AND submission_deadline >= CURRENT_DATE
    AND rfq_title ILIKE '%solar%'
    ORDER BY submission_deadline ASC;
    """





