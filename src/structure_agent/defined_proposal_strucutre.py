def proposal_structure() -> dict:
    return {
        "type": "full_proposal",
        "sections": {
            "Introduction": [],
            "Company Profile and Competencies": [
                "Organizational Capacity",
                "Domain Experience",
                "Specialized Expertise"
            ],
            "Technical Approach": {
                "subsections": ["Work Phases"],
                "lot_titles": [
                    "LOT 1: Preparation & Setup",
                    "LOT 2: Core Implementation",
                    "LOT 3: Commissioning & Handover"
                ]
            },
            "Project Management and Reporting": [
                "Project Timeline",
                "Coordination and Communication",
                "Final Deliverables"
            ],
            "Commercial": [
                "Detailed Cost Breakdown",
                "Payment Terms"
            ],
            "Team Composition": [
                "Key Personnel",
                "Local Partnerships"
            ],
            "Quality Assurance and Risk Management": [
                "Quality Assurance",
                "Risk Management"
            ],
            "Warranty and After-Sales Support": [
                "Warranty Terms",
                "Support Services"
            ],
            "Conclusion": [
                "Summary of Proposal",
                "commitment to Quality",
                "Commitment to Timeliness",
                "Next Steps"

            ],
            "Attachments": []
        },
        "attachments": True
    }
