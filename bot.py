import telebot
from telebot import types
import threading
import time
import random

bot = telebot.TeleBot("8271927017:AAEyjfOynu3rTjBRghZuIilRIackWbbPfpU")

# Dictionary to store active reminders
active_reminders = {}

# Reminder message
reminder_message = "🚨 Buy now before presale ends! Whales 🐳 are coming, fill your bags! 🚨"

# Additional messages
additional_messages = [
    "🔥 iFart burns 1.5% of every transaction - increasing scarcity!",
    "💎 Diamond hands get rewarded when paper hands sell!",
    "🎮 Earn tokens by playing our Telegram mini-app!",
    "📈 3% transaction tax (1.5% burned, 1.5% to liquidity)",
    "🔒 All rewards have 6-month vesting for stability"
]

# FAQ content
faq_content = {
    # Tokenomics
    "Token Supply": "💰 Total supply: 1B $iFART\n- 30% Mini-App Rewards\n- 20% Locked Liquidity\n- 15% Airdrops\n- 10% Team (3yr vesting)",
    "Tax Structure": "📊 3% transaction tax:\n🔥 1.5% permanently burned\n💧 1.5% to liquidity pool",
    
    # Features
    "Mini-App": "🎮 Telegram mini-app features:\n- Daily spin wheel\n- Social tasks\n- Crypto quizzes\n- Fart Rain events",
    
    # Investment
    "How to Buy": "🛒 Purchase steps:\n1) Get BNB\n2) Swap on our DEX\n3) HODL for rewards\n🌐 [Official Website](https://ifarttoken.com)",
    "Why Invest?": "💎 Unique value:\n- Viral Telegram integration\n- Anti-whale mechanics\n- 90% user retention\n🎯 1B user target",
    
    # Roadmap
    "Next Milestone": "🚀 At 50K users:\n- DEX launch\n- Public trading\n- Auto-rewards"
}

# Official links
official_links = {
    "Website": "https://ifarttoken.com",
    "Telegram": "https://t.me/ifartofficial",
    "Twitter": "https://twitter.com/ifarttoken",
    "Whitepaper": "https://ifarttoken.com/whitepaper"
}

# ======================
# KEYBOARD CONSTRUCTORS
# ======================

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [
        types.KeyboardButton('⏰ 10min Reminder'),
        types.KeyboardButton('⏰ 30min Reminder'),
        types.KeyboardButton('⏰ 1hr Reminder'),
        types.KeyboardButton('🛑 Stop Reminders'),
        types.KeyboardButton('ℹ️ Project Info')
    ]
    markup.add(*buttons)
    return markup

def faq_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    categories = [
        ("💰 Tokenomics", "faq_tokenomics"),
        ("🎮 Features", "faq_features"),
        ("🚀 Investment", "faq_investment"),
        ("📅 Roadmap", "faq_roadmap")
    ]
    for text, callback in categories:
        markup.add(types.InlineKeyboardButton(text, callback_data=callback))
    return markup

def contact_keyboard():
    markup = types.InlineKeyboardMarkup()
    for text, url in official_links.items():
        markup.add(types.InlineKeyboardButton(text, url=url))
    return markup

# ======================
# MESSAGE HANDLERS
# ======================

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_msg = """🚀 iFart Reminder Bot 💨

Set price alerts and get project updates!

*Main Controls:*
- ⏰ Set reminders
- 🛑 Stop reminders
- ℹ️ Project details"""
    
    bot.send_message(message.chat.id, welcome_msg, 
                   reply_markup=main_keyboard(),
                   parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == 'ℹ️ Project Info')
def show_info_menu(message):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("❓ FAQ", callback_data="show_faq"),
        types.InlineKeyboardButton("📞 Contact", callback_data="show_contact")
    )
    bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "show_faq")
def show_faq(call):
    bot.edit_message_text("📚 Frequently Asked Questions",
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=faq_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("faq_"))
def show_faq_category(call):
    category = call.data.split("_")[1]
    
    category_questions = {
        "tokenomics": ["Token Supply", "Tax Structure"],
        "features": ["Mini-App"],
        "investment": ["How to Buy", "Why Invest?"],
        "roadmap": ["Next Milestone"]
    }
    
    markup = types.InlineKeyboardMarkup()
    for question in category_questions[category]:
        markup.add(types.InlineKeyboardButton(question, callback_data=f"answer_{question}"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="show_faq"))
    
    bot.edit_message_text(f"📖 {category.capitalize()} Questions",
                         call.message.chat.id,
                         call.message.message_id,
                         reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("answer_"))
def show_answer(call):
    question = call.data.split("_", 1)[1]
    answer = faq_content[question]
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back to Questions", callback_data=f"faq_{get_category(question)}"))
    
    bot.send_message(call.message.chat.id, 
                    f"*{question}*\n\n{answer}",
                    parse_mode='Markdown',
                    reply_markup=markup)

def get_category(question):
    for cat, questions in {
        "tokenomics": ["Token Supply", "Tax Structure"],
        "features": ["Mini-App"],
        "investment": ["How to Buy", "Why Invest?"],
        "roadmap": ["Next Milestone"]
    }.items():
        if question in questions:
            return cat
    return "tokenomics"

@bot.callback_query_handler(func=lambda call: call.data == "show_contact")
def show_contact(call):
    bot.edit_message_text("📞 Official Links:",
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=contact_keyboard())

# ======================
# REMINDER SYSTEM
# ======================

@bot.message_handler(func=lambda m: m.text in ['⏰ 10min Reminder', '⏰ 30min Reminder', '⏰ 1hr Reminder'])
def set_reminder(message):
    chat_id = message.chat.id
    
    # Cancel existing reminder
    if chat_id in active_reminders:
        active_reminders[chat_id].cancel()
    
    # Set new reminder
    interval = {
        '10min': 600,
        '30min': 1800,
        '1hr': 3600
    }[message.text.split()[1].lower()]
    
    active_reminders[chat_id] = RepeatedTimer(interval, send_reminder, chat_id)
    
    # Smart confirmation message
    emoji = random.choice(["🚀", "💎", "🔥", "🤑"])
    duration = message.text.split()[1]
    bot.reply_to(message, f"{emoji} {duration} alerts activated!\n\nI'll remind you to watch for whale movements.")

@bot.message_handler(func=lambda m: m.text == '🛑 Stop Reminders')
def stop_reminders(message):
    chat_id = message.chat.id
    if chat_id in active_reminders:
        active_reminders[chat_id].cancel()
        del active_reminders[chat_id]
        bot.reply_to(message, "🔕 Reminders stopped. You can relax now!")
    else:
        bot.reply_to(message, "No active reminders to stop.")

def send_reminder(chat_id):
    try:
        msg = f"{reminder_message}\n\n{random.choice(additional_messages)}"
        bot.send_message(chat_id, msg, parse_mode='Markdown')
    except Exception as e:
        print(f"Reminder error: {e}")

# ======================
# TIMER CLASS
# ======================

class RepeatedTimer:
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = threading.Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def cancel(self):
        self._timer.cancel()
        self.is_running = False

if __name__ == '__main__':
    print("🤖 Bot is running...")
    bot.infinity_polling()
