import os
import logging
import asyncio
import re
import hashlib
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    JobQueue
)
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration
DOCUMENT_ID = '1wodxtiMwKBadOd8DoZpFccyqbMWRRCB8GgUEL-dFJHY'
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
SERVICE_ACCOUNT_FILE = 'service-account.json'
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
UPDATE_INTERVAL = 300  # 5 minutes in seconds
ADMIN_IDS = [6089861817, 5584801763, 7697559889]  # Your admin IDs

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class DocumentManager:
    def __init__(self):
        self.content = ""
        self.last_hash = ""
        self.last_updated = None
        self.lock = asyncio.Lock()
        self.credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        self.service = build('docs', 'v1', credentials=self.credentials)
        self.reminder_message = "🚨 iFart Token Alert! 🚨\n\nBuy now before presale ends! Whales 🐳 are coming!"

    async def update_document(self):
        """Fetch and update document content from Google Docs"""
        try:
            async with self.lock:
                document = self.service.documents().get(documentId=DOCUMENT_ID).execute()
                doc_elements = document.get('body', {}).get('content', [])
                
                new_content = ""
                for element in doc_elements:
                    if 'paragraph' in element:
                        for para_element in element['paragraph']['elements']:
                            if 'textRun' in para_element:
                                new_content += para_element['textRun']['content']
                
                content_hash = hashlib.md5(new_content.encode()).hexdigest()
                if content_hash != self.last_hash:
                    self.content = new_content
                    self.last_hash = content_hash
                    self.last_updated = datetime.now()
                    logger.info("Document content updated successfully")
                    return True
                return False
                
        except HttpError as e:
            logger.error(f"Google Docs API error: {e}")
        except Exception as e:
            logger.error(f"Error updating document: {e}")
        return False

    async def get_response(self, query: str) -> str:
        """Generate response based on document content"""
        try:
            if not self.content:
                return "Document not loaded yet. Please try again later."
            
            query = query.lower().strip()
            paragraphs = [p.strip() for p in self.content.split('\n') if p.strip()]
            
            # Check for Q&A pairs first
            for i, para in enumerate(paragraphs):
                if para.lower().startswith('q:') and query in para[2:].lower():
                    if i+1 < len(paragraphs) and paragraphs[i+1].startswith('A:'):
                        return paragraphs[i+1][2:].strip()
            
            # Check for keyword matches
            keywords = re.findall(r'\w+', query)
            best_match = ""
            best_score = 0
            
            for para in paragraphs:
                para_lower = para.lower()
                score = sum(1 for kw in keywords if kw in para_lower)
                
                if score > best_score:
                    best_match = para
                    best_score = score
            
            return best_match if best_match else "I no sabi that one. Try ask am another way."
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Error processing your request. Try again later."

# Initialize document manager
doc_manager = DocumentManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with options"""
    keyboard = [
        [InlineKeyboardButton("10 min reminder", callback_data='10'),
         InlineKeyboardButton("30 min reminder", callback_data='30')],
        [InlineKeyboardButton("1 hour reminder", callback_data='60')],
        [InlineKeyboardButton("Refresh Content", callback_data='refresh')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    last_updated = doc_manager.last_updated.strftime("%Y-%m-%d %H:%M:%S") if doc_manager.last_updated else "never"
    
    await update.message.reply_text(
        f"🤖 iFart Token Bot\n\n"
        f"Last updated: {last_updated}\n\n"
        "Ask me anything or set reminders:",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user questions"""
    try:
        response = await doc_manager.get_response(update.message.text)
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("Error don happen. Try again small time.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    
    if query.data in ['10', '30', '60']:
        # Set reminder
        minutes = int(query.data)
        context.job_queue.run_once(
            send_reminder, 
            minutes * 60, 
            chat_id=chat_id,
            data={"message": doc_manager.reminder_message}
        )
        await query.edit_message_text(text=f"⏰ Reminder set for {minutes} minutes!")
    elif query.data == 'refresh':
        # Refresh content
        was_updated = await doc_manager.update_document()
        if was_updated:
            await query.edit_message_text(text="✅ Document content refreshed!")
        else:
            await query.edit_message_text(text="ℹ️ No new updates in document")

async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send reminder message"""
    try:
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text=context.job.data["message"]
        )
    except Exception as e:
        logger.error(f"Error sending reminder: {e}")

async def scheduled_updates(context: ContextTypes.DEFAULT_TYPE):
    """Scheduled document updates"""
    try:
        logger.info("Running scheduled document update...")
        was_updated = await doc_manager.update_document()
        if was_updated:
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text="📝 iFart Token Doc updated! Bot has new info."
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")
    except Exception as e:
        logger.error(f"Scheduled update error: {e}")

async def initialize(app: Application):
    """Initialize the bot"""
    try:
        await doc_manager.update_document()
        logger.info("Initial document load complete")
    except Exception as e:
        logger.error(f"Initial document load failed: {e}")

def main() -> None:
    """Start the bot"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Schedule background tasks
    if application.job_queue:
        application.job_queue.run_repeating(
            scheduled_updates,
            interval=UPDATE_INTERVAL,
            first=10
        )
    
    # Run the bot
    application.run_polling(
        on_startup=initialize,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()
