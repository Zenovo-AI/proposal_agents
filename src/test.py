from database.db_helper import save_metadata_to_db, insert_document  # <-- make sure insert_document exists

# First insert the document entry
insert_document(
    doc_id="test_doc_minimal",
    file_name="minimal.pdf",
    file_content="Minimal document content here"
)

# Now insert the metadata
data = {
    "id": "test_doc_minimal",
    "organization_name": "Minimal Org",
    "rfq_number": "000",
    "rfq_title": "Minimal RFQ",
    "submission_deadline": None,
    "country_or_region": "Nowhere",
    "filename": "minimal.pdf"
}

save_metadata_to_db(data)