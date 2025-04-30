from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError


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


class GoogleDriveAPI:
    """
    Handles Google Drive operations such as retrieving templates and organizing files.
    """

    def __init__(self, service):
        self.service = service

    def get_template_id(self, template_name):
        """
        Find the template file ID in Google Drive by name.
        Searches for both Google Docs and .docx formats.
        """
        try:
            query = f"(name='{template_name}' and mimeType='application/vnd.google-apps.document')"  # Google Docs format
            
            response = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, mimeType)'
            ).execute()

            return response['files'][0]['id']
        
        except (KeyError, IndexError):
            raise ValueError(f"Template '{template_name}' not found in Google Drive")


    def create_folder(self, folder_name, parent_folder_id=None):
        """
        Creates a folder in Google Drive if it doesn't already exist.
        """
        try:
            # ✅ Check if the folder already exists
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"

            existing = self.service.files().list(
                q=query,
                fields='files(id)'
            ).execute().get('files', [])

            if existing:
                return existing[0]['id']  # Return existing folder ID

            # ✅ Create a new folder
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id] if parent_folder_id else []
            }
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            return folder['id']

        except HttpError as e:
            print(f"Folder creation failed: {e}")
            raise
