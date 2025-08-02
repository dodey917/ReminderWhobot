import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from gdocs_integration import GoogleDocsReader
import asyncio
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '8271927017:AAEyjfOynu3rTjBRghZuIilRIackWbbPfpU')
GOOGLE_DOCS_ID = os.getenv('GOOGLE_DOCS_ID', '1wodxtiMwKBadOd8DoZpFccyqbMWRRCB8GgUEL-dFJHY')
SERVICE_ACCOUNT_FILE = 'reminderwhobot-2c10c31bf2ce.json'

# Initialize Google Docs reader
gdocs_reader = GoogleDocsReader(SERVICE_ACCOUNT_FILE, GOOGLE_DOCS_ID)

# User reminders storage
user_reminders = {}

# Reminder message
REMINDER_MESSAGE = "Buy now before presale end, whale � are coming, fill your bag now."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with the inline keyboard when the command /start is issued."""
    keyboard = [
        [
            InlineKeyboardButton("10min Reminder", callback_data="10"),
            InlineKeyboardButton("30min Reminder", callback_data="30"),
            InlineKeyboardButton("1hr Reminder", callback_data="60"),
        ],
        [
            InlineKeyboardButton("Stop Reminders", callback_data="stop"),
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Welcome to the Reminder Bot! Choose your reminder interval:",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "stop":
        if user_id in user_reminders:
            user_reminders[user_id]['active'] = False
            if user_reminders[user_id]['task']:
                user_reminders[user_id]['task'].cancel()
            await query.edit_message_text(text="Reminders stopped!")
        else:
            await query.edit_message_text(text="No active reminders to stop.")
    else:
        try:
            minutes = int(data)
            if user_id in user_reminders and user_reminders[user_id]['active']:
                user_reminders[user_id]['task'].cancel()
            
            # Schedule the reminder
            user_reminders[user_id] = {
                'active': True,
                'interval': minutes,
                'task': asyncio.create_task(send_reminders(user_id, minutes, context.bot))
            }
            
            await query.edit_message_text(
                text=f"Reminder set for every {minutes} minutes!",
                reply_markup=query.message.reply_markup
            )
        except ValueError:
            await query.edit_message_text(text="Invalid option selected.")

async def send_reminders(user_id: int, interval_minutes: int, bot) -> None:
    """Send periodic reminders to the user."""
    try:
        while True:
            await asyncio.sleep(interval_minutes * 60)
            
            # Check if reminders are still active for this user
            if user_id not in user_reminders or not user_reminders[user_id]['active']:
                break
                
            try:
                await bot.send_message(user_id, REMINDER_MESSAGE)
            except Exception as e:
                logger.error(f"Failed to send reminder to user {user_id}: {e}")
                break
    except asyncio.CancelledError:
        logger.info(f"Reminders cancelled for user {user_id}")
    except Exception as e:
        logger.error(f"Error in reminder task for user {user_id}: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any text message by fetching response from Google Docs."""
    try:
        user_message = update.message.text
        logger.info(f"Received message from user {update.effective_user.id}: {user_message}")
        
        # Get response from Google Docs
        response = await gdocs_reader.get_response(user_message)
        
        if response:
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("I couldn't find a response for that question.")
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("Sorry, I encountered an error processing your request.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and handle them gracefully."""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and hasattr(update, 'message'):
        try:
            await update.message.reply_text("Sorry, something went wrong. Please try again.")
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

def main() -> None:
    """Start the bot."""
    try:
        # Create the Application
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_error_handler(error_handler)
        
        # Start the bot
        logger.info("Starting bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    main()
