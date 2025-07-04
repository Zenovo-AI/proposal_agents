"""
Processes various document types (TXT, PDF, Webpages) to extract and clean text content.

Functions:
- `extract_txt_content`: Extracts text from a TXT file.
- `extract_text_and_tables_from_pdf`: Extracts text and tables from a PDF file.
- `preprocess_document`: Preprocesses PDF documents by extracting text and tables.
- `process_webpage`: Extracts and cleans text content from a webpage using trafilatura.
"""


from langchain_core.documents.base import Document # type: ignore
import trafilatura # type: ignore
from utils import clean_text
import logging
import pdfplumber #type: ignore
import fitz #type: ignore

logging.basicConfig(level=logging.INFO)

class DocumentProcessor:
    def __init__(self):
        pass

    def extract_text_from_pdf(self, filepath):
        doc = fitz.open(filepath)
        text = "\n".join([page.get_text() for page in doc])
        doc.close()
        return text[:10000]


    # Helper function to read text from a TXT file
    def extract_txt_content(self, file_path):
        try:
            with open(file_path, "r") as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Error reading TXT file: {e}")
    
    

    def extract_text_and_tables_from_pdf(self, file):
        text = ""
        table_texts = []

        with pdfplumber.open(file) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # Extract text
                page_text = page.extract_text()
                if page_text:
                    text += f"\n\n[Page {page_num}]\n{page_text}"
                
                # Extract tables
                page_tables = page.extract_tables()
                for table_idx, table in enumerate(page_tables):
                    table_str = f"\n\n[Page {page_num} - Table {table_idx + 1}]\n"
                    for row in table:
                        cleaned_row = [cell if cell is not None else "" for cell in row]  # Replace None with ""
                        table_str += " | ".join(cleaned_row) + "\n"
                    table_texts.append(table_str)

        # Combine extracted text and tables
        full_text = text + "\n\n".join(table_texts)
        return full_text

    
    def preprocess_document(self, file):
        """
        Preprocess the document by extracting all text.
        """
        pdf_text = self.extract_text_and_tables_from_pdf(file)
        # Return the entire content as a single Document object
        documents = [Document(page_content=pdf_text)]
        return documents

    def process_webpage(self, url):
        """
        Download and extract text content from a webpage using trafilatura.
        """
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            web_page = trafilatura.extract(downloaded)
            return clean_text(web_page) if web_page else None
        else:
            logging.error(f"Failed to fetch webpage: {url}")
            return None