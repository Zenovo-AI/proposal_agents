# from database.db_helper import save_metadata_to_db, insert_document  # <-- make sure insert_document exists

# # First insert the document entry
# insert_document(
#     doc_id="test_doc_minimal",
#     file_name="minimal.pdf",
#     file_content="Minimal document content here"
# )

# # Now insert the metadata
# data = {
#     "id": "test_doc_minimal",
#     "organization_name": "Minimal Org",
#     "rfq_number": "000",
#     "rfq_title": "Minimal RFQ",
#     "submission_deadline": None,
#     "country_or_region": "Nowhere",
#     "filename": "minimal.pdf"
# }


# save_metadata_to_db(data)

# def cleanText(text, censorList):
#     censor_text_list = []
#     for word in text.split():
#         if word.lower().strip('!?.') in censorList:
#             censor_text_list.append("****")
#         else:
#             censor_text_list.append(word)
#     return " ".join(censor_text_list)

# # theText = ['A', 'baby', 'donkey', 'is', 'called', 'an', 'ass', 'not', 'an', 'idiot']
# theText = "A baby donkey is called an ass not an idiot!"
# theCensorList = ["ass", "idiot"]

# censored_text = cleanText(theText, theCensorList)
# print(censored_text)

from structure_agent.defined_proposal_strucutre import proposal_structure
from utils import generate_explicit_query
from pprint import pprint



if __name__ == "__main__":
    user_query = "What is CDGA's approach to rehabilitating the existing borehole?"
    print("user_query:", repr(user_query))
    structure_proposal = proposal_structure()

    print("Testing generate_explicit_query...")
    queries = generate_explicit_query(user_query, structure_proposal)
    pprint(queries)

