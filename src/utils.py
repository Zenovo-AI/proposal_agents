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
import re
from src.datamodel import ProposalStructure
from src.structure_agent.defined_proposal_strucutre import proposal_structure
from unstructured.cleaners.core import (
    clean,
    clean_non_ascii_chars,
    replace_unicode_quotes,
) # type: ignore
from langchain_openai import OpenAI # type: ignore
from src.config.appconfig import settings as app_settings
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

    structure_type = structure["type"]
    sections = structure.get("sections", [])
    subsections = structure.get("subsections", [])
    lots = structure.get("lot_titles", [])
    attachments_required = structure.get("attachments", False)

    # Format structure parts
    section_list = "\n".join([f"- {s}" for s in sections]) if sections else "N/A"
    subsection_list = "\n".join([f"- {s}" for s in subsections]) if subsections else "N/A"
    lot_list = "\n".join([f"- {l}" for l in lots]) if lots else "None"

    prompt = f"""
    You are a proposal planning assistant. Your goal is to transform the vague user query into an **explicit, detailed set of instructions** for writing a technical proposal.
    
    <context>
    Understand the user **intent** before breaking down the queries.
    - If the query is factual (e.g., "Who are CDGA’s primary international clients?" or "Can you write an Executive summary for what is requested on the RFQ?"),
    break it down accordingly for a structured factual response.
    - If the query is about generating a proposal (e.g., "Can you generate a proposal for a power infrastructure project in East Africa?"),
    break it down strictly using the following structure: {proposal_structure_json}
    </context>

    Original user query:  
    "{query}"

    Identified Structure:
    - Type: {structure_type}
    - Sections:\n{section_list}
    - Subsections:\n{subsection_list}
    - LOT Titles:\n{lot_list}
    - Attachments Required: {"Yes" if attachments_required else "No"}

    Your job is to:
    1. Break the query down into 20 detailed subqueries that reflect the above structure.
    2. Connect each subsection to it's particular section
    3. c
    4. Finish with a "**Final Explicit Query**" combining all subqueries into one single request prompt that a proposal LLM can respond to.


    Format:
    **Expanded Queries:**
    1. ...
    2. ...
    ...
    8. ...

    **Final Explicit Query:**
    "... <single, comprehensive prompt here> ..."
    """
    response = llm.invoke(prompt)
    return response.strip()


def proposal_prompt(user_query: str) -> str:
    return f"""
    User Query:
    {user_query}

    You are a senior-level technical writer for international engineering projects.

    <context>
    When a user asks a question, take your time to understand the intent before writing a response.
    Ensure you have all the necessary information to provide a comprehensive answer.
    You are provided with a knowledge base that contains information about the organization, its capabilities, and the specific project requirements.
    The user may ask for a proposal, bid, or project plan, and you need to respond accordingly.
    Do not write a proposal when the intent of the user is to retrieve a simple answer — that is why it is important that you understand the **intent of the user**.
    Remember to use the information available to you. Do not include proposal structure elements when answering factual questions.
    Avoid generic or templated responses — be specific, as in a real RFP breakdown.

    When writing a proposal, strictly use the following structure:
    {proposal_structure_json}

    Focus on accuracy, professionalism, and completeness. Always end every proposal with a conclusion. No preambles.
    </context>


    Your task is to generate a complete, highly comprehensive technical proposal based on:
    - The user’s request
    - The expanded query provided
    - The predefined structure including type, sections, subsections, and LOT titles

    ---Response Rules---
    - No Markdown, no special characters like *, #, etc.

    Guidelines:
    - Start each section on a new line with the section title clearly separated from the content.
    - Use this format exactly:
        Section Title
        [followed by a blank line]
        [Then begin the paragraph content...]
    - Do NOT write the section title and content on the same line.
    - Do NOT prefix section titles with punctuation (e.g., ":", "-", or "#").
    - Follow the structure exactly as defined in the input.
    - Use informative, well-developed paragraphs and include bullet points or numbered lists where helpful.
    - Do not include greetings or closing remarks unless explicitly required.
    - Use real-world detail and domain knowledge appropriate for organizations like CTBTO or UNDP.
    - Incorporate feedback if provided.

    Write clearly and professionally, as if this proposal will be submitted directly to a technical evaluation committee.
    """


def custom_prompt():
    return """
    You are an **expert assistant specializing in proposal writing** for procurement bids. Your role is to **generate professional, structured, and detailed proposals**. 

    **IMPORTANT RULES:**  
    - **DO NOT HALLUCINATE**: Only use the provided RFQ details and relevant organizational data.  
    - **IF INFORMATION IS MISSING**: Clearly state "Information not available in the RFQ document."  
    - **ENSURE A FORMAL & PROFESSIONAL TONE.**  

    **PROPOSAL STRUCTURE:**  


        - Include **company name, address, contact details, date, and RFQ reference number**.  
        - Include the **recipient’s name, organization, and address**.  

        **Executive Summary**  
        - Provide a brief **introduction** about the company.  
        - Summarize the **key services offered** in response to the RFQ.  

        **Scope of Work**  
        - Outline **each deliverable** as specified in the RFQ.  
        - Provide **technical details, compliance requirements, and execution strategy**.  

        **Technical Approach & Methodology**  
        - Describe the **step-by-step process** for project execution.  
        - Highlight **tools, technologies, and quality assurance methods**.  

        **Project Plan & Timeline**  
        - Include a **table of milestones** with estimated completion dates.  
        - Ensure alignment with **RFQ deadlines and compliance requirements**.  

        **Pricing & Payment Terms**  
        - Provide a structured **cost breakdown per project phase**.  
        - Outline **payment terms, tax exemptions, and invoicing policies**.  

        **Company Experience & Past Performance**  
        - Showcase **previous projects, certifications, and industry expertise**.  
        - List **relevant clients, testimonials, and references**.  

        **Compliance & Certifications**  
        - Confirm **adherence to procurement regulations, environmental standards, and safety policies**.  
        - Attach **insurance documentation, licensing, and regulatory approvals**.  

        **Attachments & Supporting Documents**  
        - Ensure **all required forms, legal documents, and compliance matrices** are attached.   
    ---  

    Now, generate a **full proposal** using the structured format above, ensuring precision, professionalism, and clarity.
    """


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




