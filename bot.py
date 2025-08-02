import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    JobQueue
)
from google.oauth2 import service_account
from googleapiclient.discovery import build
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
DOCUMENT_ID = '1wodxtiMwKBadOd8DoZpFccyqbMWRRCB8GgUEL-dFJHY'
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
SERVICE_ACCOUNT_FILE = 'service-account.json'
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '8271927017:AAEyjfOynu3rTjBRghZuIilRIackWbbPfpU')

# Initialize Google Docs service
try:
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('docs', 'v1', credentials=creds)
    document = service.documents().get(documentId=DOCUMENT_ID).execute()
    doc_content = document.get('body', {}).get('content', [])
except Exception as e:
    logger.error(f"Error accessing Google Doc: {e}")
    doc_content = []

def extract_text_from_doc():
    """Extract text from Google Doc content."""
    text = ""
    for element in doc_content:
        if 'paragraph' in element:
            for paragraph_element in element['paragraph']['elements']:
                if 'textRun' in paragraph_element:
                    text += paragraph_element['textRun']['content']
    return text

doc_text = extract_text_from_doc()

# Suggested questions based on document content
suggested_questions = [
    "What is iFart Token?",
    "How does iFart Token work?",
    "What are the benefits of iFart Token?",
    "How can I buy iFart Token?",
    "When is the presale ending?",
    "What makes iFart Token unique?"
]

# Reminder message
REMINDER_MESSAGE = "🚨 iFart Token Alert! �\n\nBuy now before presale ends! Whales 🐳 are coming, fill your bag now!\n\nDon't miss out on this golden opportunity! 💨💨💨"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("10 min", callback_data='10'),
            InlineKeyboardButton("30 min", callback_data='30'),
            InlineKeyboardButton("1 hour", callback_data='60'),
        ],
        [
            InlineKeyboardButton("Start Reminders", callback_data='start_reminders'),
            InlineKeyboardButton("Stop Reminders", callback_data='stop_reminders'),
        ],
        [
            InlineKeyboardButton("Read Document", callback_data='read_doc'),
            InlineKeyboardButton("Suggested Questions", callback_data='suggested_questions'),
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Welcome to iFart Token Mini App! 🚀💨\n\n"
        "Set reminders or get information about iFart Token:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    
    if query.data in ['10', '30', '60']:
        # Set one-time reminder
        minutes = int(query.data)
        context.job_queue.run_once(send_reminder, minutes * 60, chat_id=chat_id)
        await query.edit_message_text(text=f"⏰ Reminder set for {minutes} minutes!")
    elif query.data == 'start_reminders':
        # Start repeating reminders
        if 'job' not in context.chat_data:
            context.chat_data['job'] = context.job_queue.run_repeating(
                send_reminder, interval=3600, first=0, chat_id=chat_id
            )
            await query.edit_message_text(text="🔔 Hourly reminders started!")
        else:
            await query.edit_message_text(text="🔔 Reminders are already running!")
    elif query.data == 'stop_reminders':
        # Stop reminders
        if 'job' in context.chat_data:
            context.chat_data['job'].schedule_removal()
            del context.chat_data['job']
            await query.edit_message_text(text="🔕 Reminders stopped!")
        else:
            await query.edit_message_text(text="🔕 No active reminders to stop!")
    elif query.data == 'read_doc':
        # Show document summary
        summary = doc_text[:1000] + "..." if len(doc_text) > 1000 else doc_text
        await query.edit_message_text(text=f"📄 Document Summary:\n\n{summary}")
    elif query.data == 'suggested_questions':
        # Show suggested questions
        questions = "\n".join([f"• {q}" for q in suggested_questions])
        await query.edit_message_text(text=f"❓ Suggested Questions:\n\n{questions}\n\nYou can ask me any of these!")

async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send reminder message."""
    await context.bot.send_message(context.job.chat_id, text=REMINDER_MESSAGE)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages and answer questions."""
    user_message = update.message.text.lower()
    answer = find_answer_in_document(user_message)
    
    if answer:
        await update.message.reply_text(answer)
    else:
        await update.message.reply_text(
            "I couldn't find an answer to that in the document. "
            "Try one of the suggested questions or ask something else!"
        )

def find_answer_in_document(query: str) -> str:
    """Search for answers in the document content."""
    keywords = re.findall(r'\w+', query.lower())
    paragraphs = doc_text.split('\n')
    best_paragraph = ""
    max_matches = 0
    
    for para in paragraphs:
        if not para.strip():
            continue
            
        matches = sum(1 for kw in keywords if kw in para.lower())
        if matches > max_matches:
            max_matches = matches
            best_paragraph = para
            
    if max_matches > 0:
        return best_paragraph[:1000]  # Limit response length
    return ""

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and notify user."""
    logger.error(msg="Exception while handling update:", exc_info=context.error)
    if update and update.message:
        await update.message.reply_text("Sorry, something went wrong. Please try again later.")

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", lambda u, c: u.message.reply_text(
        "Use /start to see the main menu. You can set reminders or ask about iFart Token."
    )))
    
    # Register button handler
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Register message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Register error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    application.run_polling()
    logger.info("Bot started and running...")

if __name__ == '__main__':
    main()
