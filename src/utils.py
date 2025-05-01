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


import re
from unstructured.cleaners.core import (
    clean,
    clean_non_ascii_chars,
    replace_unicode_quotes,
)
from langchain_openai import OpenAI
from src.config.appconfig import settings as app_settings



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


def generate_explicit_query(query):
    """Expands the user query and merges expanded queries into a single, explicit query."""
    llm = OpenAI(temperature=0, openai_api_key=app_settings.openai_api_key)

    prompt = f"""
    Given the following vague query:

    '{query}'

    Expand this query into **seven structured subqueries** that break down the proposal into detailed components.
    Ensure that the query includes **specific details** such as:
    - The sender's company name, address, email, and phone number.
    - The recipient’s name, position, organization, and address.
    - A structured breakdown of the proposal, including scope of work, compliance, pricing, experience, and additional documents.

    Example:

    **Original Query:** "Can you write a proposal based on the requirements in the RFQ?"

    **Expanded Queries:**
    1. "Provide a formal header section with the sender's full company details (name, address, email, phone) and the recipient's details (name, position, organization, address)."
    2. "Write a professional opening paragraph that introduces the company and states the purpose of the proposal."
    3. "Describe the scope of work, breaking it into detailed sections for each service category (e.g., borehole rehabilitation and new drilling)."
    4. "Provide a clear breakdown of pricing, including cost per lot and total project cost, specifying currency and payment terms."
    5. "Outline a detailed project plan and timeline, including key milestones and deliverables."
    6. "List all required compliance details, including adherence to RFQ terms, delivery timelines, insurance coverage, and taxation requirements."
    7. "Outline the company's experience and qualifications, listing past projects, certifications, and key personnel expertise."
    8. "List all necessary additional documents, such as bidder’s statement, vendor profile form, and statement of confirmation, etc."

    **Final Explicit Query:**  
    "Can you write a proposal based on the requirements in the RFQ, including:  
    (1) A formal header with sender and recipient details,  
    (2) An introduction stating the company’s expertise and purpose of the proposal,  
    (3) A detailed scope of work for each service component,  
    (4) A structured pricing breakdown with currency and payment terms,  
    (5) A detailed project plan and timeline with milestones, and
    (6) A section on compliance, including delivery, insurance, and taxation,  
    (7) A section on experience and qualifications, highlighting past projects and key personnel, and  
    (8) A section listing all required additional documents."

    Now, generate an explicit query for:

    '{query}'
    """

    response = llm.invoke(prompt)
    return response.strip()


def proposal_prompt():
    return """
    You are an expert proposal assistant. Generate a comprehensive proposal using ONLY information from these sources:
    ---Knowledge Base---
    {context_data}

    ---Response Rules---
    1. Do NOT use Markdown or special characters like `**`, `#`, or `-`. Use plain text formatting only.
    2. Structure the proposal with clear section titles, separated by newlines.
    3. NO placeholders like [Company Name]; use real data from the knowledge base or note it as missing if not found.
    4. Use a professional tone.
    5. SKIP COMPLIMENTARY CLOSINGS OR VALEDICTIONS
    6. SKIP SALUTATION

    ---Proposal Structure---
    LETTERHEAD &  
    - Display brand name, reg/vat numbers, and contact info  

    INTRODUCTION 
    - Greet the recipient briefly and outline purpose

    PROJECT SCOPE  
    - Detailed scope from the knowledge base  

    EXCLUSIONS  
    - List any out-of-scope items if mentioned  

    DELIVERABLES  
    - Clearly outline what will be delivered  

    COMMERCIAL 
    - Provide cost breakdown and payment terms in a tabular form  

    SCHEDULE  
    - Timeline or milestone details 

    COMPLIANCE SECTION
    - List all required compliance details, including adherence to RFQ terms, delivery timelines, insurance coverage, and taxation requirements.


    EXPERIENCE & QUALIFICATIONS
    - Outline the company's experience and qualifications, listing past projects, certifications, and key personnel expertise.

    ADDITIONAL DOCUMENTS REQUIRED 
    - List all necessary additional documents, such as bidder’s statement, vendor profile form, and statement of confirmation, etc.

    CONCLUSION
    - Summarize key points   

    Yours Sincerely,
    - Provide sign-off lines referencing Directors or authorized persons.

    Current RFQ Requirements: {query}
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
