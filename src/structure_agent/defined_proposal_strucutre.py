# def proposal_structure() -> dict:
#     return {
#         "type": "full_proposal",
#         "sections": {
#             "Submitted by": [],
#             "Introduction": [],
#             "Understanding of the Assignment": [],
#             "Company Profile and Competencies": [
#                 "Organizational Capacity",
#                 "Domain Experience",
#                 "Specialized Expertise"
#             ],
#             "Technical Approach": {
#                 "subsections": ["Work Phases"],
#                 "Phases": [
#                     "Phase 1: Feasibility and Site Assessment",
#                     "Phase 2: System Design and Technical Specifications",
#                     "Phase 3: Tendering Support",
#                     "Phase 4: Installation Supervision",
#                     "Phase 5: Post-Installation Audit and Handover"
#                 ]
#             },
#             "Project Management and Reporting": [
#                 "Project Timeline",
#                 "Coordination and Communication",
#                 "Final Deliverables"
#             ],
#             "Commercial": [
#                 "Detailed Cost Breakdown",
#                 "Payment Terms"
#             ],
#             "Team Composition": [
#                 "Key Personnel",
#                 "Local Partnerships"
#             ],
#             "Quality Assurance and Risk Management": [
#                 "Quality Assurance",
#                 "Risk Management"
#             ],
#             "Warranty and After-Sales Support": [
#                 "Warranty Terms",
#                 "Support Services"
#             ],
#             "Conclusion": [
#                 "Summary of Proposal",
#                 "commitment to Quality",
#                 "Commitment to Timeliness",
#                 "Next Steps"

#             ],
#             "Attachments": []
#         },
#         "attachments": True
#     }



def proposal_structure() -> dict:
    return {
        "type": "full_proposal",
        "sections": {
            "Submitted by": [],
            "Introduction": [],
            "Understanding of the Assignment": [],
            "Company Profile and Competencies": {
                "subsections": [
                    "Organizational Capacity",
                    "Domain Experience",
                    "Specialized Expertise"
                ]
            },
            "Technical Approach": {
                "subsections": [
                    "Work Phases"
                ],
                "phases": [
                    "Phase 1: Feasibility and Site Assessment",
                    "Phase 2: System Design and Technical Specifications",
                    "Phase 3: Tendering Support",
                    "Phase 4: Installation Supervision",
                    "Phase 5: Post-Installation Audit and Handover"
                ]
            },
            "Project Management and Reporting": {
                "subsections": [
                    "Project Timeline",
                    "Coordination and Communication",
                    "Final Deliverables"
                ]
            },
            "Commercial": {
                "subsections": [
                    "Detailed Cost Breakdown",
                    "Payment Terms"
                ]
            },
            "Team Composition": {
                "subsections": [
                    "Key Personnel",
                    "Local Partnerships"
                ]
            },
            "Quality Assurance and Risk Management": {
                "subsections": [
                    "Quality Assurance",
                    "Risk Management"
                ]
            },
            "Warranty and After-Sales Support": {
                "subsections": [
                    "Warranty Terms",
                    "Support Services"
                ]
            },
            "Conclusion": {
                "subsections": [
                    "Summary of Proposal",
                    "Commitment to Quality",
                    "Commitment to Timeliness",
                    "Next Steps"
                ]
            },
            "Attachments": []
        },
        "attachments": True
    }
