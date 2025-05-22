import json
import logging
import re
from googleapiclient.discovery import Resource # type: ignore
from googleapiclient.errors import HttpError # type: ignore


def debug_find_placeholders(docs_service, doc_id):
        """
        Fetch the document and print detected text content to check if placeholders exist.
        """
        try:
            doc = docs_service.documents().get(documentId=doc_id).execute()
            content = doc.get("body", {}).get("content", [])

            detected_text = []
            for element in content:
                if "paragraph" in element:
                    for text_run in element["paragraph"].get("elements", []):
                        if "textRun" in text_run:
                            detected_text.append(text_run["textRun"]["content"])

            print("\n--- Detected Text in Google Doc ---\n")
            print("\n".join(detected_text))  # Print all detected text in the document
            print("\n--- End of Document Text ---\n")

        except HttpError as e:
            print(f"Error fetching document: {e}")


class GoogleDocsHelper:
    """
    Handles Google Docs integration using template-based approach.
    """

    def __init__(self, docs_service, drive_service):
        if not isinstance(docs_service, Resource) or not isinstance(drive_service, Resource):
            raise ValueError("Requires valid Docs and Drive service instances")
        self.docs_service = docs_service
        self.drive_service = drive_service

    def create_from_template(self, template_id, replacements, document_name):
        """
        Copies a Google Docs template, replaces placeholders, and returns the new document ID.
        """
        try:
            # ✅ Step 1: Copy the existing Google Docs template
            copied_file = self.drive_service.files().copy(
                fileId=template_id,
                body={"name": document_name}
            ).execute()
            new_doc_id = copied_file["id"]

            # ✅ Step 2: Fetch document content for debugging
            debug_find_placeholders(self.docs_service, new_doc_id)

            # ✅ Step 3: Build text replacement requests
            requests = []
            for placeholder, content in replacements.items():
                requests.append({
                    "replaceAllText": {
                        "containsText": {"text": f"{{{placeholder}}}", "matchCase": True},
                        "replaceText": content or "[MISSING CONTENT]"
                    }
                })

            # ✅ Step 4: Execute text replacement
            self.docs_service.documents().batchUpdate(
                documentId=new_doc_id,
                body={"requests": requests}
            ).execute()

            return new_doc_id  # Returns the Google Docs file ID

        except HttpError as e:
            print(f"❌ Error creating document from template: {e}")
            raise

    def copy_template(self, template_id, new_title):
        """Copy the template to a new document with the given title."""
        copied_file = self.drive_service.files().copy(
            fileId=template_id,
            body={"name": new_title}
        ).execute()
        return copied_file["id"]


    def replace_placeholder(self, doc_id, placeholder, replacement_text):
        document = self.docs_service.documents().get(documentId=doc_id).execute()
        requests = []
        for content in document.get("body").get("content"):
            text_elements = content.get("paragraph", {}).get("elements", [])
            for el in text_elements:
                text_run = el.get("textRun")
                if text_run and placeholder in text_run.get("content", ""):
                    start_idx = el["startIndex"]
                    end_idx = el["endIndex"]
                    requests.append({
                        "deleteContentRange": {
                            "range": {"startIndex": start_idx, "endIndex": end_idx}
                        }
                    })
                    requests.append({
                        "insertText": {
                            "location": {"index": start_idx},
                            "text": replacement_text
                        }
                    })
                    break

        if requests:
            self.docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={"requests": requests}
            ).execute()



    def generate_view_link(self, file_id):
        """
        Generates a shareable Google Drive link to view the Google Doc file.
        """
        try:
            # ✅ Set file permissions to allow viewing
            self.drive_service.permissions().create(
                fileId=file_id,
                body={"role": "reader", "type": "anyone"},
                fields="id"
            ).execute()

            # ✅ Get the file's view link
            file = self.drive_service.files().get(fileId=file_id, fields="webViewLink").execute()
            return file.get("webViewLink")

        except HttpError as e:
            print(f"Error generating view link: {e}")
            return None


