import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
import httpx

logger = logging.getLogger(__name__)

class GoogleDocsReader:
    def __init__(self, service_account_file, document_id):
        self.service_account_file = service_account_file
        self.document_id = document_id
        self.service = None
        
    async def initialize(self):
        """Initialize the Google Docs service."""
        try:
            creds = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=['https://www.googleapis.com/auth/documents.readonly']
            )
            self.service = build('docs', 'v1', credentials=creds)
            logger.info("Google Docs service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Docs service: {e}")
            raise

    async def get_document_content(self):
        """Fetch the entire content of the Google Doc."""
        if not self.service:
            await self.initialize()
            
        try:
            document = self.service.documents().get(documentId=self.document_id).execute()
            content = []
            
            for element in document.get('body', {}).get('content', []):
                if 'paragraph' in element:
                    for para_element in element['paragraph']['elements']:
                        if 'textRun' in para_element:
                            content.append(para_element['textRun']['content'])
            
            return ' '.join(content).strip()
        except HttpError as e:
            logger.error(f"Google Docs API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching document content: {e}")
            return None

    async def get_response(self, user_query):
        """Get a response based on the user's query from the Google Doc."""
        try:
            content = await self.get_document_content()
            if not content:
                return None
                
            # Simple implementation: look for lines that start with the user's query
            lines = content.split('\n')
            user_query_lower = user_query.lower()
            
            for line in lines:
                if ':' in line:
                    question, answer = line.split(':', 1)
                    if user_query_lower in question.lower():
                        return answer.strip()
                        
            # If no direct match, return the first few lines as a fallback
            return "\n".join(lines[:3])
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return None
