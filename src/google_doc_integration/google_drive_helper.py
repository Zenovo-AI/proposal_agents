from googleapiclient.errors import HttpError

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




    

