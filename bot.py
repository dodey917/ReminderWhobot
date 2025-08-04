import telebot
from telebot import types
import threading
import time

bot = telebot.TeleBot("8271927017:AAEyjfOynu3rTjBRghZuIilRIackWbbPfpU")

# Dictionary to store active reminders
active_reminders = {}

# Reminder message
reminder_message = "🚨 Buy now before presale end, whale 🐳 are coming, fill your bag now! 🚨"

# Additional messages
additional_messages = [
    "🔥 iFart token is deflationary - every transaction burns tokens increasing scarcity! 🔥",
    "💎 Holders get rewarded when paper hands sell - diamond hands win in iFart ecosystem! 💎",
    "🎮 Play the iFart mini-app on Telegram to earn tokens while having fun! �"
]

# FAQ content from whitepaper
faq_content = {
    "What is iFart Token?": "iFart is a groundbreaking meme token designed to revolutionize crypto economics through strategic tokenomics and community-driven utility. Built on a deflationary model, iFart rewards long-term holders while penalizing panic sellers, creating a self-sustaining ecosystem.",
    "How does the deflationary mechanism work?": "Every transaction incurs a 3% tax, split into two critical actions:\n- 1.5% permanently burned (removed from circulation)\n- 1.5% added to Liquidity Pool (strengthening price stability)\nThis creates scarcity and increases token value over time.",
    "What is the iFart Mini-App?": "Hosted on Telegram, the iFart Mini-App gamifies earning with features like:\n- Spin Wheel: Daily spins for random $iFART rewards\n- Social Tasks: Earn for sharing memes and inviting friends\n- Quizzes: Crypto-trivia challenges\n- Fart Rain: Catch falling 'farts' in real-time events\nAll rewards have a 6-month vesting period.",
    "What's the token distribution?": "Tokenomics:\n- Total Supply: 1,000,000,000 $iFART\n- Mini-App Rewards: 30%\n- Liquidity Pool: 20% (locked 2 years)\n- Community Airdrops: 15%\n- Team/Dev: 10% (vested over 3 years)",
    "What's the roadmap?": "Roadmap phases:\n1. Foundation & Initial Launch (Current Stage)\n2. Mobile Expansion & On-Chain Presence\n3. Liquidity, Trading & Holder Rewards\n4. Ecosystem Maturity & Long-Term Value\nEach phase activates at specific user milestones (10K, 30K, 50K, 100K users)."
}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    
    # Reminder buttons
    btn_10min = types.KeyboardButton('⏰ 10min Reminder')
    btn_30min = types.KeyboardButton('⏰ 30min Reminder')
    btn_1hr = types.KeyboardButton('⏰ 1hr Reminder')
    btn_stop = types.KeyboardButton('🛑 Stop Reminders')
    
    # FAQ buttons (first 3 questions)
    faq_buttons = list(faq_content.keys())[:3]
    btn_faq1 = types.KeyboardButton(faq_buttons[0])
    btn_faq2 = types.KeyboardButton(faq_buttons[1])
    btn_faq3 = types.KeyboardButton(faq_buttons[2])
    btn_more_faq = types.KeyboardButton('❓ More Questions')
    
    markup.add(btn_10min, btn_30min, btn_1hr, btn_stop, 
               btn_faq1, btn_faq2, btn_faq3, btn_more_faq)
    
    welcome_msg = """Welcome to iFart Reminder Bot! 🚀💨

Use the buttons to:
- Set reminders to buy before whales 🐳 come
- Get answers to common questions
- Stop reminders when needed

Remember: Paper hands fuel your gains; diamond hands grow their bags! 💎"""
    
    bot.send_message(message.chat.id, welcome_msg, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ['⏰ 10min Reminder', '⏰ 30min Reminder', '⏰ 1hr Reminder'])
def set_reminder(message):
    chat_id = message.chat.id
    
    # Cancel any existing reminder
    if chat_id in active_reminders:
        active_reminders[chat_id].cancel()
    
    # Determine interval
    if '10min' in message.text:
        interval = 600  # 10 minutes in seconds
    elif '30min' in message.text:
        interval = 1800  # 30 minutes
    else:
        interval = 3600  # 1 hour
    
    # Create and start reminder
    active_reminders[chat_id] = RepeatedTimer(interval, send_reminder, chat_id)
    bot.reply_to(message, f"✅ Reminder set for every {message.text.split()[1]}! You'll be notified to fill your bags.")

@bot.message_handler(func=lambda message: message.text == '🛑 Stop Reminders')
def stop_reminders(message):
    chat_id = message.chat.id
    if chat_id in active_reminders:
        active_reminders[chat_id].cancel()
        del active_reminders[chat_id]
        bot.reply_to(message, "🛑 Reminders stopped! You can set new ones anytime.")
    else:
        bot.reply_to(message, "You don't have any active reminders to stop.")

@bot.message_handler(func=lambda message: message.text == '❓ More Questions')
def more_questions(message):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    
    # Get remaining FAQ questions (skip first 3)
    faq_buttons = list(faq_content.keys())[3:]
    for question in faq_buttons:
        markup.add(types.KeyboardButton(question))
    
    markup.add(types.KeyboardButton('🔙 Back to Main'))
    
    bot.send_message(message.chat.id, "Here are more questions about iFart Token:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '🔙 Back to Main')
def back_to_main(message):
    send_welcome(message)

@bot.message_handler(func=lambda message: message.text in faq_content)
def answer_question(message):
    question = message.text
    answer = faq_content[question]
    bot.reply_to(message, answer)

def send_reminder(chat_id):
    # Send the reminder message plus a random additional message
    import random
    full_message = f"{reminder_message}\n\n{random.choice(additional_messages)}"
    bot.send_message(chat_id, full_message)

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

print("Bot is running...")
bot.infinity_polling()
