import telebot
from telebot import types
import threading
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build
import re
import random

# Configuration
TOKEN = '8271927017:AAEyjfOynu3rTjBRghZuIilRIackWbbPfpU'
GOOGLE_DOC_ID = '1wodxtiMwKBadOd8DoZpFccyqbMWRRCB8GgUEL-dFJHY'
SERVICE_ACCOUNT_FILE = 'telegrambotoauth-9663d74b6c50.json'

bot = telebot.TeleBot(TOKEN)
user_data = {}

class GoogleDocParser:
    def __init__(self):
        self.doc_content = ""
        self.sections = {}
        self.last_updated = 0
        self.refresh_interval = 3600  # 1 hour
        
    def refresh_content(self):
        """Force refresh the document content"""
        self.last_updated = 0
        return self.get_doc_content()
        
    def get_doc_content(self):
        """Fetch and cache the Google Doc content"""
        current_time = time.time()
        if current_time - self.last_updated > self.refresh_interval:
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    SERVICE_ACCOUNT_FILE,
                    scopes=['https://www.googleapis.com/auth/documents.readonly']
                )
                
                service = build('docs', 'v1', credentials=credentials)
                doc = service.documents().get(documentId=GOOGLE_DOC_ID).execute()
                
                content = []
                current_section = None
                section_content = []
                
                for elem in doc.get('body', {}).get('content', []):
                    if 'paragraph' in elem:
                        paragraph = elem['paragraph']
                        # Check if this is a section heading
                        if 'headingId' in paragraph.get('paragraphStyle', {}):
                            if current_section:
                                self.sections[current_section] = '\n'.join(section_content)
                            current_section = ''.join(
                                e['textRun']['content'] for e in paragraph['elements'] 
                                if 'textRun' in e
                            ).strip()
                            section_content = []
                        else:
                            for text_run in paragraph.get('elements', []):
                                if 'textRun' in text_run:
                                    text = text_run['textRun']['content']
                                    content.append(text)
                                    if current_section:
                                        section_content.append(text)
                
                if current_section:
                    self.sections[current_section] = '\n'.join(section_content)
                
                self.doc_content = ''.join(content).strip()
                self.last_updated = current_time
                
                # If no sections were found, create default ones
                if not self.sections:
                    self._create_default_sections()
                    
            except Exception as e:
                print(f"Error fetching Google Doc: {e}")
                if not self.doc_content:
                    self.doc_content = "Buy now before presale end, whale 🐳 are coming, fill your bag now"
                    self._create_default_sections()
        
        return self.doc_content
    
    def _create_default_sections(self):
        """Create default sections if none found"""
        self.sections = {
            "Disclaimer": re.search(r'DISCLAIMER(.+?)(?=\n\d\.|\Z)', self.doc_content, re.DOTALL).group(1).strip() 
                        if re.search(r'DISCLAIMER(.+?)(?=\n\d\.|\Z)', self.doc_content, re.DOTALL) 
                        else "No disclaimer found",
            "Brief Intro": re.search(r'1\. Brief Intro(.+?)(?=\n\d\.|\Z)', self.doc_content, re.DOTALL).group(1).strip() 
                          if re.search(r'1\. Brief Intro(.+?)(?=\n\d\.|\Z)', self.doc_content, re.DOTALL) 
                          else "No introduction found",
            "Tokenomics": re.search(r'(Tokenomics|Economic.+\n)(.+?)(?=\n\d\.|\Z)', self.doc_content, re.DOTALL|re.IGNORECASE).group(2).strip() 
                        if re.search(r'(Tokenomics|Economic.+\n)(.+?)(?=\n\d\.|\Z)', self.doc_content, re.DOTALL|re.IGNORECASE) 
                        else "No tokenomics found",
            "Roadmap": re.search(r'(Roadmap|Future Plans.+\n)(.+?)(?=\n\d\.|\Z)', self.doc_content, re.DOTALL|re.IGNORECASE).group(2).strip() 
                     if re.search(r'(Roadmap|Future Plans.+\n)(.+?)(?=\n\d\.|\Z)', self.doc_content, re.DOTALL|re.IGNORECASE) 
                     else "No roadmap found"
        }
    
    def find_answer(self, question):
        """Search for answers in the document based on the question"""
        content = self.get_doc_content()
        question_lower = question.lower()
        
        # Check for specific questions
        if any(q in question_lower for q in ['what is ifart', 'about ifart', 'tell me about ifart']):
            return self._format_answer("Brief Intro", self.sections.get("Brief Intro", "No information available about iFart."))
        
        elif any(q in question_lower for q in ['tokenomics', 'economic', 'token model', 'supply']):
            return self._format_answer("Tokenomics", self.sections.get("Tokenomics", "No tokenomics information available."))
        
        elif any(q in question_lower for q in ['disclaimer', 'risk', 'legal']):
            return self._format_answer("Disclaimer", self.sections.get("Disclaimer", "No disclaimer information available."))
        
        elif any(q in question_lower for q in ['roadmap', 'plan', 'future', 'milestone']):
            return self._format_answer("Roadmap", self.sections.get("Roadmap", "No roadmap information available."))
        
        elif any(q in question_lower for q in ['mini-app', 'mini app', 'telegram game']):
            return self._get_mini_app_info()
        
        elif any(q in question_lower for q in ['how to buy', 'where to buy', 'get ifart']):
            return self._get_buying_info()
        
        elif any(q in question_lower for q in ['team', 'developer', 'who created']):
            return self._get_team_info()
        
        elif any(q in question_lower for q in ['supply', 'total supply', 'circulating']):
            return self._get_supply_info()
        
        elif any(q in question_lower for q in ['tax', 'fee', 'transaction cost']):
            return self._get_tax_info()
        
        # If no specific match, try to find relevant sections
        for section, section_content in self.sections.items():
            if question_lower in section.lower():
                return self._format_answer(section, section_content)
        
        # Default response
        return self._get_random_response(question)
    
    def _format_answer(self, title, content):
        """Format the answer with a title and content"""
        return f"**{title}**\n\n{content[:2000]}{'...' if len(content) > 2000 else ''}"
    
    def _get_mini_app_info(self):
        """Get information about the mini-app"""
        content = self.get_doc_content()
        mini_app_match = re.search(r'(Mini-App|Telegram Game|Earn While You Play)(.+?)(?=\n\d\.|\Z)', content, re.DOTALL|re.IGNORECASE)
        if mini_app_match:
            return self._format_answer("Mini-App Information", mini_app_match.group(2).strip())
        return "The iFart Mini-App is a Telegram-based game where you can earn $iFART tokens through various activities like spinning wheels, completing social tasks, quizzes, and catching falling 'farts' in real-time events."
    
    def _get_buying_info(self):
        """Get information about buying iFart"""
        return ("You can buy $iFART tokens through our official DEX once it launches. "
                "Check the roadmap for updates on exchange listings. "
                "Always ensure you're using official links to avoid scams.")
    
    def _get_team_info(self):
        """Get information about the team"""
        return ("The iFart team is a group of anonymous developers passionate about "
                "combining meme culture with sustainable tokenomics. The team allocation "
                "is 10% of total supply, vested over 3 years to ensure long-term commitment.")
    
    def _get_supply_info(self):
        """Get information about token supply"""
        supply_match = re.search(r'Total Supply\s*([\d,]+)\s*\$iFART', self.doc_content)
        if supply_match:
            return f"The total supply of $iFART is {supply_match.group(1)} tokens."
        return "The total supply of $iFART is 1,000,000,000 tokens with a deflationary burn mechanism."
    
    def _get_tax_info(self):
        """Get information about transaction taxes"""
        tax_match = re.search(r'Transaction Tax\s*(\d+%)', self.doc_content)
        if tax_match:
            return f"Each transaction has a {tax_match.group(1)} tax, split between token burns and liquidity pool contributions."
        return "Each transaction has a 3% tax (1.5% burned, 1.5% added to liquidity pool)."
    
    def _get_random_response(self, question):
        """Generate a random response for unrecognized questions"""
        responses = [
            "I found this information that might help:",
            "Here's what I know about that:",
            "Based on the whitepaper:",
            "The document mentions:",
            "Relevant information:"
        ]
        
        # Try to find any matching content
        content = self.get_doc_content()
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', content)
        relevant_sentences = [s for s in sentences if any(word.lower() in s.lower() for word in question.split())]
        
        if relevant_sentences:
            return f"{random.choice(responses)}\n\n{'. '.join(relevant_sentences[:3])}"
        
        # Fallback to general info
        general_topics = [
            "Brief Intro", "Tokenomics", "Roadmap", "Mini-App Features"
        ]
        topic = random.choice(general_topics)
        return (f"I'm not sure about that specific question, but here's some information "
                f"about {topic}:\n\n{self.sections.get(topic, 'No information available')}")

doc_parser = GoogleDocParser()

# Predefined questions for user suggestions
PRE_DEFINED_QUESTIONS = [
    "What is iFart?",
    "Can you explain the tokenomics?",
    "What's the transaction tax?",
    "How does the mini-app work?",
    "What's the total supply?",
    "Tell me about the roadmap",
    "What are the current milestones?",
    "How can I earn iFart tokens?",
    "Is there a vesting period?",
    "What's the disclaimer?",
    "Who created iFart?",
    "How do I buy iFart?",
    "What exchanges list iFart?",
    "Explain the burn mechanism",
    "What's the liquidity pool?",
    "How many users does iFart have?",
    "What's the retention rate?",
    "Tell me about the team allocation",
    "What are the community rewards?",
    "How does the deflationary model work?",
    "What's the long-term vision?",
    "Are there any partnerships?",
    "What makes iFart different?",
    "How does the spin wheel work?",
    "What are social tasks?",
    "Explain the fart rain game",
    "What's the vesting period for rewards?",
    "How often are tokens burned?",
    "What's the LP boost?",
    "How does iFart prevent pump and dump?",
    "What's the target market cap?",
    "How many active users are there?",
    "What's the Telegram integration?",
    "Explain the meme token revolution",
    "What are the holder benefits?",
    "How does scarcity create value?",
    "What's the passive growth mechanism?",
    "Explain the anti-pump/dump features",
    "What's the mini-app reward system?",
    "How do daily spins work?",
    "What are the social tasks rewards?",
    "Explain the quiz rewards",
    "How does the real-time event work?",
    "What's the vesting model?",
    "How does the 6-month vesting work?",
    "What's the user acquisition strategy?",
    "How viral is iFart?",
    "What's the retention strategy?",
    "Explain the community-first focus",
    "What meme contests exist?",
    "How do leaderboards work?",
    "What are Squad collaborations?",
    "What's Phase 1 of the roadmap?",
    "What happens at 10,000 users?",
    "What's Phase 2 about?",
    "What's the mobile expansion plan?",
    "When does the DEX launch?",
    "What happens at 50,000 users?",
    "What's Phase 3 about?",
    "What top-tier listings are planned?",
    "How will liquidity be boosted?",
    "When do auto-payouts start?",
    "When will public trading begin?",
    "What's Phase 4 about?",
    "How often are deflationary burns?",
    "What's the iFart Swap?",
    "Explain the staking platform",
    "What's the total token supply?",
    "What percentage goes to mini-app rewards?",
    "How much is in the liquidity pool?",
    "What are community airdrops?",
    "How much is allocated to team/dev?",
    "Why should I hold iFart?",
    "What's the built-in demand?",
    "How does deflationary pressure work?",
    "Explain the viral flywheel",
    "What's the 1B user goal?",
    "What are the legal considerations?",
    "Is iFart regulated?",
    "What jurisdictions is iFart available in?",
    "Are there any guarantees?",
    "How often is the roadmap updated?",
    "What's the long-term vision?",
    "How does iFart compare to other meme coins?",
    "What's the competitive advantage?",
    "How is the team compensated?",
    "What's the vesting for team tokens?",
    "How transparent is the project?",
    "Where can I check the smart contract?",
    "Is the LP locked?",
    "For how long is the LP locked?",
    "What's the transaction speed?",
    "Which blockchain is iFart on?",
    "What are the gas fees?",
    "How eco-friendly is iFart?",
    "What's the community size?",
    "How active is the community?",
    "Where can I join the community?",
    "Are there any official social channels?",
    "How can I contact the team?",
    "Is there a whitepaper?",
    "Where can I read more?",
    "How often is the document updated?",
    "What's the most recent update?",
    "How do I get the latest information?"
]

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    
    # Main control buttons
    btn_row1 = [
        types.KeyboardButton('Start Reminders'),
        types.KeyboardButton('Stop Reminders')
    ]
    btn_row2 = [
        types.KeyboardButton('10 min reminders'),
        types.KeyboardButton('30 min reminders'),
        types.KeyboardButton('1 hour reminders')
    ]
    btn_row3 = [
        types.KeyboardButton('Refresh Content'),
        types.KeyboardButton('Suggested Questions')
    ]
    
    for btn in btn_row1:
        markup.add(btn)
    for btn in btn_row2:
        markup.add(btn)
    for btn in btn_row3:
        markup.add(btn)
    
    current_message = doc_parser.get_doc_content()[:500] + "..." if len(doc_parser.get_doc_content()) > 500 else doc_parser.get_doc_content()
    
    bot.send_message(
        message.chat.id,
        "🚀 Welcome to the Official iFart Information Bot! 🚀\n\n"
        "I can provide detailed information from the iFart whitepaper and send you regular reminders.\n\n"
        "🔹 Ask me anything about iFart tokenomics, roadmap, or features\n"
        "🔹 Use buttons to control reminder settings\n"
        "🔹 Click 'Refresh Content' to get the latest from the whitepaper\n"
        "🔹 Try 'Suggested Questions' for quick info\n\n"
        f"📄 Current document preview:\n{current_message}",
        reply_markup=markup,
        parse_mode='Markdown'
    )
    
    # Initialize user data if not exists
    if message.chat.id not in user_data:
        user_data[message.chat.id] = {
            'active': False,
            'interval': 1800,  # default 30 min
            'timer': None
        }

@bot.message_handler(commands=['refresh'])
def handle_refresh_command(message):
    """Handle the /refresh command to update content"""
    chat_id = message.chat.id
    doc_parser.refresh_content()
    bot.send_message(chat_id, "📢 Document content refreshed with the latest version from Google Docs!")

@bot.message_handler(func=lambda message: message.text in [
    'Start Reminders', 'Stop Reminders', 
    '10 min reminders', '30 min reminders', 
    '1 hour reminders', 'Refresh Content',
    'Suggested Questions'
])
def handle_buttons(message):
    chat_id = message.chat.id
    
    if chat_id not in user_data:
        user_data[chat_id] = {
            'active': False,
            'interval': 1800,
            'timer': None
        }
    
    if message.text == 'Start Reminders':
        if not user_data[chat_id]['active']:
            user_data[chat_id]['active'] = True
            start_reminders(chat_id)
            bot.send_message(chat_id, "🔔 Reminders started! You'll now receive regular updates.", parse_mode='Markdown')
        else:
            bot.send_message(chat_id, "🔔 Reminders are already running!", parse_mode='Markdown')
    
    elif message.text == 'Stop Reminders':
        if user_data[chat_id]['active']:
            user_data[chat_id]['active'] = False
            if user_data[chat_id]['timer']:
                user_data[chat_id]['timer'].cancel()
            bot.send_message(chat_id, "⏹ Reminders stopped.", parse_mode='Markdown')
        else:
            bot.send_message(chat_id, "⏹ Reminders aren't running!", parse_mode='Markdown')
    
    elif message.text == '10 min reminders':
        user_data[chat_id]['interval'] = 600
        bot.send_message(chat_id, "⏰ Reminder interval set to 10 minutes", parse_mode='Markdown')
        if user_data[chat_id]['active']:
            if user_data[chat_id]['timer']:
                user_data[chat_id]['timer'].cancel()
            start_reminders(chat_id)
    
    elif message.text == '30 min reminders':
        user_data[chat_id]['interval'] = 1800
        bot.send_message(chat_id, "⏰ Reminder interval set to 30 minutes", parse_mode='Markdown')
        if user_data[chat_id]['active']:
            if user_data[chat_id]['timer']:
                user_data[chat_id]['timer'].cancel()
            start_reminders(chat_id)
    
    elif message.text == '1 hour reminders':
        user_data[chat_id]['interval'] = 3600
        bot.send_message(chat_id, "⏰ Reminder interval set to 1 hour", parse_mode='Markdown')
        if user_data[chat_id]['active']:
            if user_data[chat_id]['timer']:
                user_data[chat_id]['timer'].cancel()
            start_reminders(chat_id)
    
    elif message.text == 'Refresh Content':
        doc_parser.refresh_content()
        content_preview = doc_parser.get_doc_content()[:500] + "..." if len(doc_parser.get_doc_content()) > 500 else doc_parser.get_doc_content()
        bot.send_message(chat_id, f"🔄 Document content refreshed!\n\nPreview:\n{content_preview}", parse_mode='Markdown')
    
    elif message.text == 'Suggested Questions':
        # Send a selection of suggested questions
        questions_markup = types.InlineKeyboardMarkup()
        
        # Add buttons in rows of 2
        for i in range(0, min(10, len(PRE_DEFINED_QUESTIONS)), 2):
            row = []
            if i < len(PRE_DEFINED_QUESTIONS):
                row.append(types.InlineKeyboardButton(
                    PRE_DEFINED_QUESTIONS[i], 
                    callback_data=f"question_{i}"
                ))
            if i+1 < len(PRE_DEFINED_QUESTIONS):
                row.append(types.InlineKeyboardButton(
                    PRE_DEFINED_QUESTIONS[i+1], 
                    callback_data=f"question_{i+1}"
                ))
            if row:
                questions_markup.add(*row)
        
        # Add "More Questions" button if there are more
        if len(PRE_DEFINED_QUESTIONS) > 10:
            questions_markup.add(types.InlineKeyboardButton(
                "More Questions →", 
                callback_data="more_questions_1"
            ))
        
        bot.send_message(
            chat_id,
            "Here are some questions you can ask about iFart:",
            reply_markup=questions_markup
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith('question_'))
def handle_question_callback(call):
    """Handle when a user clicks a suggested question"""
    question_idx = int(call.data.split('_')[1])
    if 0 <= question_idx < len(PRE_DEFINED_QUESTIONS):
        question = PRE_DEFINED_QUESTIONS[question_idx]
        answer = doc_parser.find_answer(question)
        bot.send_message(call.message.chat.id, f"❓ **Question:** {question}\n\n{answer}", parse_mode='Markdown')
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('more_questions_'))
def handle_more_questions(call):
    """Handle pagination for suggested questions"""
    page = int(call.data.split('_')[2])
    start_idx = page * 10
    end_idx = min((page + 1) * 10, len(PRE_DEFINED_QUESTIONS))
    
    questions_markup = types.InlineKeyboardMarkup()
    
    # Add buttons for this page
    for i in range(start_idx, end_idx, 2):
        row = []
        if i < len(PRE_DEFINED_QUESTIONS):
            row.append(types.InlineKeyboardButton(
                PRE_DEFINED_QUESTIONS[i], 
                callback_data=f"question_{i}"
            ))
        if i+1 < len(PRE_DEFINED_QUESTIONS):
            row.append(types.InlineKeyboardButton(
                PRE_DEFINED_QUESTIONS[i+1], 
                callback_data=f"question_{i+1}"
            ))
        if row:
            questions_markup.add(*row)
    
    # Add navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton(
            "← Previous", 
            callback_data=f"more_questions_{page-1}"
        ))
    if end_idx < len(PRE_DEFINED_QUESTIONS):
        nav_buttons.append(types.InlineKeyboardButton(
            "Next →", 
            callback_data=f"more_questions_{page+1}"
        ))
    if nav_buttons:
        questions_markup.add(*nav_buttons)
    
    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=questions_markup
    )
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_questions(message):
    chat_id = message.chat.id
    question = message.text
    
    # Don't process button commands as questions
    if message.text in [
        'Start Reminders', 'Stop Reminders', 
        '10 min reminders', '30 min reminders', 
        '1 hour reminders', 'Refresh Content',
        'Suggested Questions'
    ]:
        return
    
    # Show typing action while processing
    bot.send_chat_action(chat_id, 'typing')
    
    answer = doc_parser.find_answer(question)
    bot.send_message(chat_id, answer, parse_mode='Markdown')

def start_reminders(chat_id):
    if user_data[chat_id]['active']:
        # Send first reminder immediately
        reminder_content = doc_parser.get_doc_content()[:2000]  # Truncate if too long
        bot.send_message(chat_id, f"🔔 Reminder:\n\n{reminder_content}", parse_mode='Markdown')
        
        # Set up the recurring reminder
        user_data[chat_id]['timer'] = threading.Timer(
            user_data[chat_id]['interval'],
            send_reminder,
            args=[chat_id]
        )
        user_data[chat_id]['timer'].start()

def send_reminder(chat_id):
    if chat_id in user_data and user_data[chat_id]['active']:
        reminder_content = doc_parser.get_doc_content()[:2000]  # Truncate if too long
        bot.send_message(chat_id, f"🔔 Reminder:\n\n{reminder_content}", parse_mode='Markdown')
        
        # Schedule the next reminder
        user_data[chat_id]['timer'] = threading.Timer(
            user_data[chat_id]['interval'],
            send_reminder,
            args=[chat_id]
        )
        user_data[chat_id]['timer'].start()

if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()
