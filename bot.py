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
import asyncio

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = '8271927017:AAEyjfOynu3rTjBRghZuIilRIackWbbPfpU'

# User reminders storage
user_reminders = {}

# Reminder messages
REMINDER_MESSAGES = [
    "Buy now before presale end, whale 🐳 are coming, fill your bag now.",
    "Don't miss out! The presale is ending soon - secure your position now!",
    "Whale alert! 🚨 Prices are about to surge - top up your bags!",
    "Last chance to buy at this price! The pump is coming soon!"
]

# iFart Token content for Q&A
IFART_CONTENT = {
    "What is iFart Token?": (
        "iFart is a groundbreaking meme token designed to revolutionize crypto economics through strategic tokenomics "
        "and community-driven utility. Built on a deflationary model, iFart rewards long-term holders while penalizing "
        "panic sellers, creating a self-sustaining ecosystem."
    ),
    "What are iFart's tokenomics?": (
        "Tokenomics:\n"
        "- Total Supply: 1,000,000,000 $iFART\n"
        "- Transaction Tax: 3% (1.5% Burn + 1.5% LP)\n"
        "- Mini-App Rewards: 30% of total supply\n"
        "- Liquidity Pool: 20% (locked for 2 years)\n"
        "- Community Airdrops: 15%\n"
        "- Team/Dev: 10% (vested over 3 years)\n\n"
        "Every transaction incurs a 3% tax split into:\n"
        "1.5% permanently burned (reducing supply)\n"
        "1.5% added to liquidity pool (strengthening price stability)"
    ),
    "What is the iFart Mini-App?": (
        "The iFart Mini-App on Telegram gamifies earning with these features:\n\n"
        "🎡 Spin Wheel: Daily spins for random $iFART rewards\n"
        "📢 Social Tasks: Share memes, invite friends, tweet for bonus tokens\n"
        "🧠 Quizzes: Crypto-trivia challenges\n"
        "💨 Fart Rain: Catch falling 'farts' in real-time events\n\n"
        "All rewards have a 6-month vesting period to ensure long-term engagement."
    ),
    "What's iFart's roadmap?": (
        "Roadmap Highlights:\n\n"
        "PHASE 1 (Current):\n"
        "- Mini-App live\n"
        "- 10K users: Wallet submission enabled\n\n"
        "PHASE 2:\n"
        "- 30K users: Standalone mobile app launch\n"
        "- 50K users: DEX launch & contract public\n\n"
        "PHASE 3 (100K users):\n"
        "- Major listings\n"
        "- Liquidity boost\n"
        "- Auto-payouts activated\n"
        "- Public trading begins\n\n"
        "PHASE 4:\n"
        "- Bi-weekly token burns\n"
        "- iFart Swap & Staking Platform"
    ),
    "Why should I hold iFart?": (
        "Key Reasons to Hold $iFART:\n\n"
        "🔥 Built-in Demand: Mini-App users constantly generate transactions\n"
        "📉 Deflationary Pressure: Burns and LP growth counter inflation\n"
        "🔄 Viral Flywheel: Gamified rewards attract new users\n"
        "🎯 1B Goal: Targeting 1 billion users by 2027 via Telegram\n\n"
        "'Paper hands fuel your gains; diamond hands grow their bags'"
    ),
    "Is iFart a good investment?": (
        "DISCLAIMER: iFart is a community experiment. Token value is driven by supply/demand dynamics, "
        "and the team makes no guarantees regarding returns.\n\n"
        "That said, iFart combines:\n"
        "- Viral meme potential\n"
        "- Sustainable tokenomics\n"
        "- Gamified earning\n"
        "- Telegram's 950M user base\n\n"
        "As with any crypto, only invest what you can afford to lose."
    )
}

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
    
    # Create question suggestions from iFart content
    question_buttons = [
        [InlineKeyboardButton(q, callback_data=f"q_{i}")] 
        for i, q in enumerate(IFART_CONTENT.keys())
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard + question_buttons)
    
    await update.message.reply_text(
        "🚀 Welcome to the iFart Reminder Bot! 💨\n\n"
        "Choose your reminder interval or ask about iFart Token:",
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
            await query.edit_message_text(text="⏹ Reminders stopped!")
        else:
            await query.edit_message_text(text="ℹ️ No active reminders to stop.")
    elif data.startswith("q_"):
        # Handle question button
        question_index = int(data[2:])
        question = list(IFART_CONTENT.keys())[question_index]
        answer = list(IFART_CONTENT.values())[question_index]
        await query.edit_message_text(
            text=f"❓ <b>{question}</b>\n\n{answer}",
            parse_mode='HTML',
            reply_markup=query.message.reply_markup
        )
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
                text=f"⏰ Reminder set for every {minutes} minutes!",
                reply_markup=query.message.reply_markup
            )
        except ValueError:
            await query.edit_message_text(text="❌ Invalid option selected.")

async def send_reminders(user_id: int, interval_minutes: int, bot) -> None:
    """Send periodic reminders to the user."""
    try:
        message_index = 0
        while True:
            await asyncio.sleep(interval_minutes * 60)
            
            # Check if reminders are still active for this user
            if user_id not in user_reminders or not user_reminders[user_id]['active']:
                break
                
            try:
                # Cycle through different reminder messages
                await bot.send_message(user_id, REMINDER_MESSAGES[message_index % len(REMINDER_MESSAGES)])
                message_index += 1
            except Exception as e:
                logger.error(f"Failed to send reminder to user {user_id}: {e}")
                break
    except asyncio.CancelledError:
        logger.info(f"Reminders cancelled for user {user_id}")
    except Exception as e:
        logger.error(f"Error in reminder task for user {user_id}: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any text message by checking against iFart content."""
    try:
        user_message = update.message.text
        logger.info(f"Received message from user {update.effective_user.id}: {user_message}")
        
        # Check if message matches any iFart content question
        for question, answer in IFART_CONTENT.items():
            if user_message.lower() in question.lower():
                await update.message.reply_text(
                    f"❓ <b>{question}</b>\n\n{answer}",
                    parse_mode='HTML'
                )
                return
        
        # If no match, show suggestions
        keyboard = [
            [InlineKeyboardButton(q, callback_data=f"q_{i}")] 
            for i, q in enumerate(IFART_CONTENT.keys())
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Here are some questions about iFart Token:",
            reply_markup=reply_markup
        )
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
        logger.info("Starting iFart Reminder Bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    main()
