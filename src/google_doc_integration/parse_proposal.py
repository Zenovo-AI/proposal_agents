# Parse generated content into template structure
import json
import logging
from google_doc_integration.extract_sections import extract_section


# Helper Function to Clean and Parse JSON
def clean_and_parse_json(raw_json):
    try:
        fixed_json = raw_json.replace("{{", "{").replace("}}", "}")
        return json.loads(fixed_json)
    except json.JSONDecodeError as e:
        logging.error(f"JSON parsing error: {e}. Raw data: {raw_json}")
        return None

def parse_proposal_content(proposal_text):
    """Extracts proposal sections with proper placeholder keys"""
    parsed_data = {
        "INTRODUCTION_CONTENT": extract_section(proposal_text, "Introduction"),
        "PROJECT_SCOPE_CONTENT": extract_section(proposal_text, "Project Scope"),
        "EXCLUSIONS_CONTENT": extract_section(proposal_text, "Exclusions"),
        "DELIVERABLES_CONTENT": extract_section(proposal_text, "Deliverables"),
        "COMMERCIAL_CONTENT": extract_section(proposal_text, "Commercial"),
        "SCHEDULE_CONTENT": extract_section(proposal_text, "Schedule"),
        "COMPLIANCE_CONTENT": extract_section(proposal_text, "Compliance Section"),
        "EXPERIENCE_CONTENT": extract_section(proposal_text, "Experience & Qualifications"),
        "ADDITIONAL_DOCUMENTS_CONTENT": extract_section(proposal_text, "Additional Documents Required"),
        "CONCLUSION_CONTENT": extract_section(proposal_text, "Conclusion"),
        "SIGN_OFF_CONTENT": extract_section(proposal_text, "Yours Sincerely,")    
    }

    # 🔍 DEBUG: Log extracted content before sending it for replacement
    print("\n--- 🔍 DEBUG: Parsed Proposal Content ---")
    for key, value in parsed_data.items():
        print(f"{key}: {value[200:]}...")  # Print first 200 characters for preview
    print("--- 🔍 End of Parsed Content ---\n")

    return parsed_data