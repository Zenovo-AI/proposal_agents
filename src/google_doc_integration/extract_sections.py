import re


def extract_section(proposal_text, section_name):
    """Robust section extraction with subsections handling"""
    lines = proposal_text.split('\n')
    content = []
    capture = False
    subsection_pattern = re.compile(r'^\s*(LOT \d+:|•|\d+\.)\s*', re.IGNORECASE)
    
    # Define section names that mark the end of the current section
    end_sections = ['Project Scope', 'Exclusions', 'Deliverables', 'Commercial', 'Schedule', 'Compliance Section', 'Experience & Qualifications', 'Additional Documents Required', 'Conclusion', 'Yours Sincerely']
    # Build regex pattern to match any of these sections at line start
    end_pattern = re.compile(
        r'^\s*({})\b.*'.format(  # \b ensures whole word match
            '|'.join(re.escape(section) for section in end_sections)
        ),
        re.IGNORECASE
    )

    for line in lines:
        # Normalize line for matching
        clean_line = line.strip().lower().replace('_', ' ').replace('/', ' ')
        
        # Start capturing at target section (exact match check)
        if section_name.lower() == clean_line and not capture:
            capture = True
            continue  # Skip the section header line itself
            
        if capture:
            # Stop at next main section (using original line for pattern matching)
            if end_pattern.match(line.strip()):
                break
                
            # Preserve subsections and lists with proper formatting
            if subsection_pattern.match(line):
                content.append('\n' + line.strip())
            elif line.strip():
                content.append(line.strip())

    return '\n'.join(content).strip()


