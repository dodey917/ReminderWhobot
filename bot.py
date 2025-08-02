import os
import logging
import asyncio
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables
load_dotenv()

# Configuration
DOCUMENT_ID = '1wodxtiMwKBadOd8DoZpFccyqbMWRRCB8GgUEL-dFJHY'
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
SERVICE_ACCOUNT_FILE = 'service-account.json'
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
UPDATE_INTERVAL = 300  # 5 minutes in seconds

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class DocumentCache:
    def __init__(self):
        self.content = ""
        self.last_updated = None
        self.lock = asyncio.Lock()

    async def update(self):
        """Update the document content from Google Docs"""
        try:
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            service = build('docs', 'v1', credentials=creds)
            
            async with self.lock:
                document = service.documents().get(documentId=DOCUMENT_ID).execute()
                doc_elements = document.get('body', {}).get('content', [])
                
                # Extract text from document elements
                new_content = ""
                for element in doc_elements:
                    if 'paragraph' in element:
                        for para_element in element['paragraph']['elements']:
                            if 'textRun' in para_element:
                                new_content += para_element['textRun']['content']
                
                self.content = new_content
                self.last_updated = datetime.now()
                logger.info("Document content updated successfully")
                
        except HttpError as e:
            logger.error(f"Google Docs API error: {e}")
        except Exception as e:
            logger.error(f"Error updating document: {e}")

    async def get_content(self):
        """Get the current document content"""
        async with self.lock:
            return self.content

    async def get_last_updated(self):
        """Get when the document was last updated"""
        async with self.lock:
            return self.last_updated

# Initialize document cache
document_cache = DocumentCache()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message"""
    keyboard = [
        [InlineKeyboardButton("Refresh Document", callback_data='refresh')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    last_updated = await document_cache.get_last_updated()
    last_updated_str = last_updated.strftime("%Y-%m-%d %H:%M:%S") if last_updated else "never"
    
    await update.message.reply_text(
        f"🤖 iFart Token Info Bot\n\n"
        f"Document last updated: {last_updated_str}\n\n"
        "Ask me anything about iFart Token and I'll find relevant info from our document!",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user questions and find answers in document"""
    user_message = update.message.text
    if not user_message:
        return
    
    try:
        content = await document_cache.get_content()
        if not content:
            await update.message.reply_text("⚠️ Document content not loaded yet. Please try again later.")
            return
        
        # Find most relevant paragraph
        answer = await find_best_answer(user_message, content)
        if answer:
            await update.message.reply_text(answer)
        else:
            await update.message.reply_text("🤷 I couldn't find relevant information for your question in the document.")
            
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("⚠️ Sorry, I encountered an error processing your request.")

async def find_best_answer(query: str, content: str) -> str:
    """Find the most relevant answer in document content"""
    try:
        # Simple keyword matching - can be enhanced with better NLP
        keywords = re.findall(r'\w+', query.lower())
        paragraphs = [p for p in content.split('\n') if p.strip()]
        
        if not paragraphs:
            return ""
        
        # Score paragraphs by keyword matches
        scored = []
        for para in paragraphs:
            score = sum(1 for kw in keywords if kw in para.lower())
            if score > 0:
                scored.append((score, para))
        
        if not scored:
            return ""
        
        # Return the best matching paragraph (limited to 1000 chars)
        best_match = max(scored, key=lambda x: x[0])[1]
        return best_match[:1000] + ("..." if len(best_match) > 1000 else "")
    
    except Exception as e:
        logger.error(f"Error finding answer: {e}")
        return ""

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all Telegram bot errors"""
    logger.error(f"Update {update} caused error: {context.error}")
    
    if isinstance(update, Update) and update.message:
        await update.message.reply_text(
            "⚠️ An error occurred. Our team has been notified. Please try again later."
        )

async def scheduled_updates(context: ContextTypes.DEFAULT_TYPE):
    """Scheduled task to update document content"""
    try:
        logger.info("Running scheduled document update...")
        await document_cache.update()
    except Exception as e:
        logger.error(f"Error in scheduled update: {e}")

async def initialize():
    """Initialize the bot and perform first document load"""
    try:
        await document_cache.update()
        logger.info("Initial document load complete")
    except Exception as e:
        logger.error(f"Initial document load failed: {e}")

def main() -> None:
    """Start the bot and schedule background tasks"""
    # Create Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    # Schedule background tasks
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(
            scheduled_updates,
            interval=UPDATE_INTERVAL,
            first=10  # Start 10 seconds after launch
        )
    
    # Run initialization and start bot
    application.run_polling(
        on_startup=initialize,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()
