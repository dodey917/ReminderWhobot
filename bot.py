import telebot
from telebot import types
import threading
import time
import random

bot = telebot.TeleBot("8271927017:AAEyjfOynu3rTjBRghZuIilRIackWbbPfpU")

# Dictionary to store active reminders
active_reminders = {}

# Reminder message
reminder_message = "🚨 Buy now before presale end, whale 🐳 are coming, fill your bag now! 🚨"

# Additional messages
additional_messages = [
    "🔥 iFart token is deflationary - every transaction burns tokens increasing scarcity! 🔥",
    "💎 Holders get rewarded when paper hands sell - diamond hands win in iFart ecosystem! 💎",
    "🎮 Play the iFart mini-app on Telegram to earn tokens while having fun! 🎮",
    "📈 Transaction tax: 3% (1.5% burned, 1.5% to liquidity pool) 📉",
    "🔒 6-month vesting period for all mini-app rewards 🔒"
]

# FAQ content from whitepaper
faq_content = {
    "What is iFart Token?": "iFart is a groundbreaking meme token designed to revolutionize crypto economics through strategic tokenomics and community-driven utility. Built on a deflationary model, iFart rewards long-term holders while penalizing panic sellers, creating a self-sustaining ecosystem.",
    
    "How does the deflationary mechanism work?": "Every transaction incurs a 3% tax, split into:\n🔥 1.5% permanently burned (removed from circulation)\n💧 1.5% added to Liquidity Pool (strengthening price stability)\nThis creates scarcity and increases token value over time.",
    
    "What is the iFart Mini-App?": "🎮 Hosted on Telegram with 500K+ users:\n- Spin Wheel: Daily token rewards\n- Social Tasks: Earn for sharing\n- Quizzes: Crypto challenges\n- Fart Rain: Real-time events\n📆 All rewards have 6-month vesting",
    
    "Token Distribution": "💰 Total Supply: 1B $iFART\n- 30% Mini-App Rewards\n- 20% Liquidity Pool (locked 2y)\n- 15% Community Airdrops\n- 10% Team/Dev (vested 3y)\n- 25% Presale/Public",
    
    "Roadmap Summary": "🛣️ Growth Phases:\n1. 10K users: Wallet submission\n2. 30K users: Mobile apps\n3. 50K users: DEX launch\n4. 100K users: Auto-payouts\n5. 1B users: Web3 ecosystem",
    
    "How to buy iFart Token?": "🛒 Purchase Steps:\n1. Get BNB in your wallet\n2. Connect to our DEX (coming at 50K users)\n3. Swap BNB for $iFART\n4. HODL for rewards!\n🌐 Website: [ifarttoken.com](https://ifarttoken.com)",
    
    "Why invest in iFart?": "💡 Unique Value:\n- Viral Telegram integration\n- Gamified earning\n- Anti-whale mechanics\n- Strong tokenomics\n- 90% user retention\n🎯 Target: 1B users by 2027",
    
    "Team & Security": "👨💻 Team:\n- Doxxed core members\n- 10% tokens vested 3 years\n🔒 Security:\n- LP locked 2 years\n- Regular smart contract audits\n- Community governance",
    
    "Presale Details": "🎟️ Presale Info:\n- 25% of total supply\n- Bonus for early participants\n- Vesting schedule applies\n⚠️ Ends soon! Fill your bags!",
    
    "Community Benefits": "🤝 Community Perks:\n- Meme contests with prizes\n- Leaderboard rewards\n- Squad collaborations\n- Governance voting\n- Exclusive NFT airdrops"
}

# Official links
official_links = {
    "🌐 Website": "https://ifarttoken.com",
    "📄 Whitepaper": "https://ifarttoken.com/whitepaper",
    "📱 Telegram": "https://t.me/ifartofficial",
    "🐦 Twitter": "https://twitter.com/ifarttoken",
    "📊 DexTools": "https://www.dextools.io/ifart"
}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    # Create main keyboard with reminder options
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_10min = types.KeyboardButton('⏰ 10min Reminder')
    btn_30min = types.KeyboardButton('⏰ 30min Reminder')
    btn_1hr = types.KeyboardButton('⏰ 1hr Reminder')
    btn_stop = types.KeyboardButton('🛑 Stop Reminders')
    btn_info = types.KeyboardButton('ℹ️ Project Info')
    markup.add(btn_10min, btn_30min, btn_1hr, btn_stop, btn_info)
    
    welcome_msg = """🚀 *Welcome to iFart Reminder Bot* 💨

*Quick Actions:*
- Set buy reminders (10min/30min/1hr)
- Stop reminders when needed
- Get project information

*Pro Tip:* Whales are accumulating! Set reminders to never miss buying opportunities!"""
    
    bot.send_message(message.chat.id, welcome_msg, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'ℹ️ Project Info')
def show_info_menu(message):
    # Create inline keyboard for info options
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_faq = types.InlineKeyboardButton("📚 FAQ & Knowledge Base", callback_data="show_faq")
    btn_links = types.InlineKeyboardButton("📞 Contact & Official Links", callback_data="show_links")
    markup.add(btn_faq, btn_links)
    
    bot.send_message(message.chat.id, 
                    "🔍 *What information do you need?*\n\nSelect an option below to learn more about iFart Token:",
                    parse_mode='Markdown',
                    reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "show_faq")
def show_faq_categories(call):
    # Create FAQ category menu
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    categories = [
        ("💰 Tokenomics", "Learn about token supply, taxes, and distribution"),
        ("🚀 Features", "Discover iFart's unique features and mini-app"),
        ("📈 Investment", "Why and how to invest in iFart"),
        ("👥 Community", "Community benefits and perks")
    ]
    
    for text, desc in categories:
        markup.add(types.InlineKeyboardButton(text, callback_data=f"faq_category:{text}"))
    
    bot.edit_message_text("*📚 iFart Knowledge Base*\n\nSelect a category to explore:",
                         call.message.chat.id,
                         call.message.message_id,
                         parse_mode='Markdown',
                         reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("faq_category:"))
def show_category_questions(call):
    category = call.data.split(":")[1]
    
    # Map categories to questions
    category_map = {
        "💰 Tokenomics": ["What is iFart Token?", "How does the deflationary mechanism work?", "Token Distribution"],
        "🚀 Features": ["What is the iFart Mini-App?", "Community Benefits"],
        "📈 Investment": ["Why invest in iFart?", "How to buy iFart Token?", "Presale Details"],
        "👥 Community": ["Community Benefits", "Team & Security"]
    }
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for question in category_map[category]:
        markup.add(types.InlineKeyboardButton(question, callback_data=f"faq:{question}"))
    
    markup.add(types.InlineKeyboardButton("🔙 Back to Categories", callback_data="show_faq"))
    
    bot.edit_message_text(f"*{category} Questions*\n\nSelect a question to view the answer:",
                         call.message.chat.id,
                         call.message.message_id,
                         parse_mode='Markdown',
                         reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("faq:"))
def show_faq_answer(call):
    question = call.data.split(":")[1]
    answer = faq_content[question]
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back to Questions", callback_data=f"faq_category:{get_category_for_question(question)}"))
    
    bot.send_message(call.message.chat.id, 
                    f"*{question}*\n\n{answer}",
                    parse_mode='Markdown',
                    reply_markup=markup)
    bot.answer_callback_query(call.id)

def get_category_for_question(question):
    category_map = {
        "💰 Tokenomics": ["What is iFart Token?", "How does the deflationary mechanism work?", "Token Distribution"],
        "🚀 Features": ["What is the iFart Mini-App?", "Community Benefits"],
        "📈 Investment": ["Why invest in iFart?", "How to buy iFart Token?", "Presale Details"],
        "👥 Community": ["Community Benefits", "Team & Security"]
    }
    for category, questions in category_map.items():
        if question in questions:
            return category
    return "💰 Tokenomics"

@bot.callback_query_handler(func=lambda call: call.data == "show_links")
def show_contact_links(call):
    # Create inline keyboard for official links
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for text, url in official_links.items():
        markup.add(types.InlineKeyboardButton(text, url=url))
    
    markup.add(types.InlineKeyboardButton("🔙 Back to Info Menu", callback_data="back_to_info"))
    
    bot.edit_message_text("📞 *Official iFart Links*\n\nConnect with us through these official channels:",
                         call.message.chat.id,
                         call.message.message_id,
                         parse_mode='Markdown',
                         reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_info")
def back_to_info_menu(call):
    show_info_menu(call.message)

@bot.message_handler(func=lambda message: message.text in ['⏰ 10min Reminder', '⏰ 30min Reminder', '⏰ 1hr Reminder'])
def set_reminder(message):
    chat_id = message.chat.id
    
    # Cancel any existing reminder
    if chat_id in active_reminders:
        active_reminders[chat_id].cancel()
        del active_reminders[chat_id]
    
    # Determine interval and confirmation message
    if '10min' in message.text:
        interval = 600
        confirm_msg = "10 minutes reminder set"
    elif '30min' in message.text:
        interval = 1800
        confirm_msg = "30 minutes reminder set"
    else:
        interval = 3600
        confirm_msg = "1 hour reminder set"
    
    # Create and start reminder
    active_reminders[chat_id] = RepeatedTimer(interval, send_reminder, chat_id)
    
    # Simple confirmation message
    bot.reply_to(message, confirm_msg)

@bot.message_handler(func=lambda message: message.text == '🛑 Stop Reminders')
def stop_reminders(message):
    chat_id = message.chat.id
    if chat_id in active_reminders:
        active_reminders[chat_id].cancel()
        del active_reminders[chat_id]
        bot.reply_to(message, "Reminders stopped")
    else:
        bot.reply_to(message, "No active reminders")

def send_reminder(chat_id):
    # Send the reminder message plus a random additional message
    full_message = f"{reminder_message}\n\n{random.choice(additional_messages)}"
    bot.send_message(chat_id, full_message, parse_mode='Markdown')

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
    print("Bot is running...")
    bot.infinity_polling()
