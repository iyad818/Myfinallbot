# cython: language_level=3
import re
import requests
from faker import Faker
import emoji
import pycountry
import string
import time
from datetime import datetime, timedelta
import telebot
from telebot.types import LabeledPrice
from telebot.types import PreCheckoutQuery
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import random

# استبدل هذا بالتوكن الخاص بك
TOKEN = "7312710877:AAHiUhIc0ip_N9c83VO9AT2R-lHub-8l0RE"
bot = telebot.TeleBot(TOKEN)
USER_LAST_BIN_REQUEST = {}
ADMINS = [7192243354, 987654321] 
VIP_FILE = "vip_data.json"
CODES_FILE = "codes.json"

# دالة لتحويل النص إلى شكل مزخرف
def fancy_text(text):
    normal_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    fancy_chars = "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳"
    translation_table = str.maketrans(normal_chars, fancy_chars)
    return text.translate(translation_table)

# دالة للهروب من المشاكل في MarkdownV2
def escape_markdown_v2(text):
    escape_chars = "_*[]()~`>#+-=|{}.!\\"
    return "".join("\\" + char if char in escape_chars else char for char in text)

@bot.message_handler(commands=["id"])
def send_user_info(message):
    user = message.from_user
    user_id = f"`{escape_markdown_v2(str(user.id))}`"
    name = f"[{escape_markdown_v2(user.first_name)}](tg://user?id={user.id})"
    username = f"@{escape_markdown_v2(user.username)}" if user.username else "لا يوجد"

    response = f"""
{fancy_text("Account Info 🪪")}

{fancy_text("ID")}: {user_id}
{fancy_text("Name")}: {name}
{fancy_text("Username")}: {username}
{fancy_text("➖➖➖➖➖➖➖➖➖")}
    """
    
    bot.send_message(message.chat.id, response, parse_mode="MarkdownV2")
with open("top_bin.json", "r", encoding="utf-8") as f:
    top_bin_data = json.load(f)

with open("flags.json", "r", encoding="utf-8") as f:
    flags_data = json.load(f)

# دالة تحقق Luhn
def luhn_generate(bin_number):
    while True:
        card_number = [int(digit) for digit in bin_number]
        while len(card_number) < 16:
            card_number.append(random.randint(0, 9))
        
        check_sum = sum(card_number[-1::-2]) + sum(sum(divmod(d * 2, 10)) for d in card_number[-2::-2])
        if check_sum % 10 == 0:
            return "".join(map(str, card_number))

# أمر /gen BIN
@bot.message_handler(commands=["gen"])
def generate_cards(message):
    args = message.text.split()

    if len(args) != 2 or not args[1].isdigit() or not (6 <= len(args[1]) <= 12):
        bot.reply_to(message, """**🚫 𝐈𝐧𝐜𝐨𝐫𝐫𝐞𝐜𝐭 𝐈𝐧𝐩𝐮𝐭! 𝐏𝐥𝐞𝐚𝐬𝐞 𝐩𝐫𝐨𝐯𝐢𝐝𝐞 𝐚 𝟔-𝟏𝟐𝐝𝐢𝐠𝐢𝐭 𝐁𝐈𝐍 𝐧𝐮𝐦𝐛𝐞𝐫!
𝐄𝐱𝐚𝐦𝐩𝐥𝐞:** `/gen 412236`""", parse_mode="Markdown")
        return

    # أخذ أول 6 أرقام فقط من BIN المدخل
    bin_number = args[1][:6]
    bin_info = top_bin_data.get(bin_number)

    if not bin_info:
        bot.reply_to(message, "❌ BIN not recognized. Please enter a valid BIN.")
        return

    msg = bot.reply_to(message, "🔄 Generating cards …")

    # توليد 10 بطاقات صالحة بالتنسيق المطلوب
    cards = [
        f"`{luhn_generate(bin_number)}|{str(random.randint(1, 12)).zfill(2)}|{random.randint(2026, 2032)}|{random.randint(100, 999)}`"
        for _ in range(10)
    ]

    # استخراج بيانات BIN
    brand = bin_info.get("scheme", "Unknown")
    card_type = bin_info.get("type", "Unknown").upper()
    bank = bin_info.get("bank", "Unknown")
    country = bin_info.get("country", "Unknown")
    flag = flags_data.get(bin_info.get("flag", ""), "🏳")

    # تنسيق الرسالة النهائية
    response = f"𝐁𝐈𝐍 ➜ `{bin_number}`\n\n" + "\n".join(cards) + f"\n\n𝐁𝐈𝐍 𝐈𝐧𝐟𝐨 ➜ `{brand} - {card_type}`\n𝐁𝐚𝐧𝐤 ➜ `{bank}`\n𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ➜ `{country}` {flag}"

    # تحديث الرسالة
    bot.edit_message_text(response, chat_id=msg.chat.id, message_id=msg.message_id, parse_mode="Markdown")
IMAGE_URL = "https://imageshack.com/i/pnGUbbvHj"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # إنشاء زر شفاف
    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton("𝗧𝗛𝗘 𝗗𝗘𝗩𝗘𝗟𝗢𝗣𝗘𝗥 🔥", url="https://t.me/iyad_ar")  # استبدل YOUR_LINK_HERE برابط المطور
    keyboard.add(button)

    # إرسال الرسالة مع الصورة والزر
    bot.send_photo(
        message.chat.id, 
        IMAGE_URL, 
        caption="""💰 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗗𝗘𝗔𝗥

𝗕𝗼𝘁 𝗦𝘁𝗮𝘁𝘂𝘀 ☑️

🚧 𝗬𝗼𝘂 𝗰𝗮𝗻 𝗮𝗱𝗱 𝗺𝗲 𝘁𝗼 𝘆𝗼𝘂𝗿 𝗴𝗿𝗼𝘂𝗽 𝗮𝗻𝗱 𝗜 𝘄𝗶𝗹𝗹 𝘄𝗼𝗿𝗸 𝘁𝗵𝗲𝗿𝗲, 𝗗𝗼𝗻'𝘁 𝗳𝗼𝗿𝘁𝗲𝗴𝘁 𝘁𝗼 𝗺𝗮𝗸𝗲 𝗺𝗲 𝗮 𝗺𝗼𝗱𝗲𝗿𝗮𝘁𝗼𝗿 ⚡ """, 
        reply_markup=keyboard
    )
with open("top_bin.json", "r", encoding="utf-8") as f:
    bin_data = json.load(f)

with open("flags.json", "r", encoding="utf-8") as f:
    country_flags = json.load(f)
@bot.message_handler(commands=["bin"])
def lookup_bin(message):
    user_id = message.from_user.id
    current_time = time.time()

    # الحماية من السبام
    if user_id in USER_LAST_BIN_REQUEST:
        time_since_last_request = current_time - USER_LAST_BIN_REQUEST[user_id]
        if time_since_last_request < 5:
            remaining_time = int(5 - time_since_last_request)
            bot.reply_to(message, f"⛔ 𝗔𝗡𝗧𝗜 𝗦𝗽𝗮𝗺 𝗗𝗲𝘁𝗲𝗰𝘁𝗲𝗱!\n\n🔄 𝗧𝗿𝘆 𝗮𝗴𝗮𝗶𝗻 𝗮𝗳𝘁𝗲𝗿 {remaining_time} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀.")
            return

    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, """🚫 𝐈𝐧𝐜𝐨𝐫𝐫𝐞𝐜𝐭 𝐈𝐧𝐩𝐮𝐭! 𝐏𝐥𝐞𝐚𝐬𝐞 𝐩𝐫𝐨𝐯𝐢𝐝𝐞 𝐚 𝟔-𝐝𝐢𝐠𝐢𝐭 𝐁𝐈𝐍 𝐧𝐮𝐦𝐛𝐞𝐫!
𝐄𝐱𝐚𝐦𝐩𝐥𝐞:|||☞ `/bin 412236`
|||☞ `/bin 4122363857295288|09|2028|340`
``` 𝐊𝐢𝐥𝐰𝐚 - 🍀```
 """, parse_mode="Markdown")
            return

        # استخراج أول 6 أرقام فقط بغض النظر عن طول الإدخال
        bin_number = re.sub(r"\D", "", args[1])[:6]

        if not bin_number.isdigit() or len(bin_number) != 6:
            bot.reply_to(message, "Please Enter BIN from 6 numbers ❌", parse_mode="Markdown")
            return

        # تسجيل وقت البحث
        USER_LAST_BIN_REQUEST[user_id] = current_time

        # إرسال رسالة "جاري البحث..."
        loading_message = bot.reply_to(message, "Searching Wait 🔎…")

        # البحث عن معلومات الـ BIN
        info = bin_data.get(bin_number)
        if not info:
            bot.edit_message_text("This BIN is not found, Sorry, choose a valid one 🚫", chat_id=message.chat.id, message_id=loading_message.message_id)
            return

        # استخراج البيانات المطلوبة
        bank_name = info.get("bank", "Unknown Bank")
        country_code = info.get("flag", "Unknown")  
        country_name = info.get("country", "Unknown Country")
        country_flag = country_flags.get(country_code, "🚩")

        result = f"""
𝗕𝗜𝗡 𝗟𝗼𝗼𝗸𝘂𝗽 𝗥𝗲𝘀𝘂𝗹𝘁 🔍

𝗕𝗜𝗡 ⇾ `{bin_number}`
------------------------------
𝗜𝗻𝗳𝗼 ⇾ `{info.get("scheme", "Unknown").upper()} - {info.get("type", "Unknown").upper()} - {info.get("brand", "Unknown")}`
------------------------------
𝐈𝐬𝐬𝐮𝐞𝐫 ⇾ `{bank_name}`
------------------------------
𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⇾ `{country_name} {country_flag}`

𝗕𝐲 🛡: [𝐊𝐢𝐥𝐰𝐚 - 🍀](https://t.me/iyad_ar)
"""
        bot.edit_message_text(result, chat_id=message.chat.id, message_id=loading_message.message_id, parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {e}")
def load_vip_data():
    try:
        with open("vip_data.json", "r") as file:
            return json.load(file)  # تحميل البيانات كـ dictionary
    except FileNotFoundError:
        return {}

# حساب الوقت المتبقي (عرض الساعات والدقائق فقط)
def time_left(expiration_time: str) -> str:
    expiration = datetime.strptime(expiration_time, "%Y-%m-%d %H:%M:%S")
    current_time = datetime.now()
    if expiration < current_time:
        return None  # الاشتراك انتهى
    remaining_time = expiration - current_time
    
    # استخراج الساعات والدقائق فقط
    hours, remainder = divmod(remaining_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}"  # تنسيق HH:MM

# التعامل مع الأمر /account
@bot.message_handler(commands=['account'])
def account(message):
    user_id = str(message.from_user.id)
    vip_data = load_vip_data()

    # طباعة محتوى vip_data لفحصه
    print(vip_data)

    if user_id in vip_data:
        expiration_time = vip_data[user_id]
        remaining_time = time_left(expiration_time)
        
        if remaining_time:
            bot.reply_to(message, f"The time remaining until your subscription expires is: {remaining_time}")
        else:
            bot.reply_to(message, "Your subscription has expired, please subscribe again 🔌")
    else:
        bot.reply_to(message, "You are not subscribed, sorry 📛")
# دالة فحص OTP
def get_bin_info(bin_number):
    try:
        response = requests.get(f"https://lookup.binlist.net/{bin_number}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

# دالة لتحويل كود الدولة إلى علم باستخدام Unicode
def get_country_flag(country_code):
    if not country_code:
        return "❌"
    return "".join(chr(127397 + ord(c)) for c in country_code.upper())

@bot.message_handler(commands=['otp'])
def otp(message):
    try:
        args = message.text.split(' ')
        if len(args) != 2:
            bot.send_message(message.chat.id, "Please provide card information in the format: <code>cc|mm|yy|cvv</code>", parse_mode='HTML')
            return

        card_info = args[1]
        card_details = card_info.split('|')

        if len(card_details) != 4:
            bot.send_message(message.chat.id, "Invalid format! Use: <code>cc|mm|yy|cvv</code>", parse_mode='HTML')
            return

        card_number, month, year, cvv = card_details
        bin_number = card_number[:6]

        # إرسال رسالة انتظار أولية
        waiting_message = bot.send_message(message.chat.id, "Checking OTP 🤔...", parse_mode='HTML')

        # قراءة ملف Bin.txt لمعرفة إن كان الـ BIN موجودًا
        try:
            with open("Bin.txt", "r") as file:
                bin_data = file.read().splitlines()
        except FileNotFoundError:
            bin_data = []

        # التحقق مما إذا كان BIN موجودًا في الملف
        if bin_number in bin_data:
            result = "𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅"
            response = "Successful payment (LookUP3DS)"
            gate = "Braintree 🔰"
        else:
            result = "𝗥𝗲𝗷𝗲𝗰𝘁𝗲𝗱 ❌"
            response = "Payment unsuccessful "
            gate = "Braintree 🔰"

        # جلب معلومات BIN من API
        bin_info = get_bin_info(bin_number)

        # تجهيز البيانات المسترجعة
        country_code = bin_info.get("country", {}).get("alpha2", "") if bin_info else ""
        country_flag = get_country_flag(country_code)
        country_name = bin_info.get("country", {}).get("name", "----") if bin_info else "----"

        result_message = f"""<b>Result:</b> {result}

<b>Card:</b> <code>{card_number}|{month}|{year}|{cvv}</code>

<b>Response:</b> {response}

<b>Gateway:</b> 3DS Lookup
<b>Gate:</b> {gate}
---
"""

        if bin_info:
            result_message += f"""<b>BIN:</b> {bin_number}
<b>Info:</b> {bin_info.get('type', '----')}
<b>Issuer:</b> {bin_info.get('bank', {}).get('name', '----')}
<b>Country:</b> {country_name} {country_flag}
<b>Other:</b> {bin_info.get('scheme', '----').upper()}
---
"""
        else:
            result_message += "<b>BIN Information:</b> Data not available ❌\n"

        result_message += "◆ 🌃◆"

        # الانتظار 3 ثوانٍ قبل تحديث الرسالة
        time.sleep(3)

        # تحديث الرسالة السابقة بدل إرسال رسالة جديدة
        bot.edit_message_text(result_message, chat_id=message.chat.id, message_id=waiting_message.message_id, parse_mode='HTML')

    except Exception as e:
        bot.send_message(message.chat.id, f"<b>Error:</b> <code>{str(e)}</code>", parse_mode='HTML')
import logging  
logging.basicConfig(level=logging.INFO)  
  
def load_vip_data():  
    try:  
        with open(VIP_FILE, 'r') as f:  
            return json.load(f)  
    except FileNotFoundError:  
        return {}  
  
def update_vip_data(data):  
    with open(VIP_FILE, 'w') as f:  
        json.dump(data, f, indent=4)  
  
def is_user_vip(user_id):  
    vip_data = load_vip_data()  
    if str(user_id) in vip_data:  
        expiry_time = datetime.strptime(vip_data[str(user_id)], '%Y-%m-%d %H:%M:%S')  
        if expiry_time > datetime.now():  
            return True  
    return False  
  
def load_bins():  
    with open('Bin.txt', 'r') as f:  
        bins = [line.strip() for line in f.readlines()]  
    return bins  
  
def luhn_check(card_number):  
    total = 0  
    reverse_digits = card_number[::-1]  
    for i, digit in enumerate(reverse_digits):  
        n = int(digit)  
        if i % 2 == 1:  
            n *= 2  
            if n > 9:  
                n -= 9  
        total += n  
    return total % 10 == 0  
  
def read_cards(file_url):  
    response = requests.get(file_url)  
    if response.status_code == 200:  
        return response.text.splitlines()  
    return []  
  
def validate_card(card, bins):  
    parts = card.split('|')  
    if len(parts) != 4:  
        return False  
    cc, mm, yy, cvv = parts  
    bin6 = cc[:6].strip()  
    return bin6 in bins and luhn_check(cc.strip())  
  
stop_checking = {}  
@bot.message_handler(content_types=['document'])  
def handle_document(message):  
    chat_id = message.chat.id  
    file_id = message.document.file_id  # استخدام file_id من الرسالة  
  
    # التحقق من الاشتراك قبل إرسال الفاتورة  
    if not is_user_vip(message.from_user.id):  
        plan_time = 1  # الاشتراك لمدة يوم واحد  
        price = 5  # تكلفة الاشتراك (بالوحدات المناسبة)  
        expire = datetime.now() + timedelta(days=plan_time)  
        prices = [LabeledPrice(label='VIP', amount=int(price * 1))]  # سعر الاشتراك بالعملة (XTR)  
  
        try:  
            # إرسال الفاتورة مباشرة  
            bot.send_invoice(  
                chat_id=chat_id,  
                title='اشتراك يوم 1 📨',  
                description="""خطة VIP المميزة ⚡  
━━━━━━━━━━━━━━━━━  
قم بالحصول وفتح كل الأدوات والبوابات وكذلك الفحص عبر الملفات وتخطي الحظر عبر هاته الخطة 😍  
انت حالتك غير مشترك 📛  
━━━━━━━━━━━━━━━━━  
قم بدفع 5 نجمة وستحصل على اشتراك لمدة يوم واحد ⚡✅  
الثمن  
5 ⭐   
♡ اكمل الدفع 🥊  
━━━━━━━━━━━━━━━━━""",  
                invoice_payload=f'{chat_id}_{expire}',  
                provider_token='YOUR_PROVIDER_TOKEN',  # يجب إدخال الـ token الخاص بمزود الدفع  
                currency='XTR',  
                prices=prices  
            )  
        except Exception as e:  
            # في حال حدوث خطأ عند إرسال الفاتورة  
            bot.send_message(chat_id, f"❌ حدث خطأ أثناء إرسال الفاتورة: {str(e)}")  
            return  
    else:  
        # إذا كان المستخدم مشتركًا بالفعل، يتم بدء الفحص  
        start_card_check(chat_id, file_id)  
  
def start_card_check(chat_id, file_id):  
    stop_checking[chat_id] = False  
  
    # التحقق من وجود الملف باستخدام file_id  
    try:  
        file_info = bot.get_file(file_id)  # استخدام file_id الصحيح هنا  
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"  
    except Exception as e:  
        bot.send_message(chat_id, f"❌ حدث خطأ في الحصول على الملف: {str(e)}")  
        return  
  
    # قراءة البطاقات  
    cards = read_cards(file_url)  
    if not cards:  
        bot.send_message(chat_id, "❌ فشل في قراءة الملف أو أنه فارغ.")  
        return  
  
    total_count = len(cards)  
  
    # إرسال رسالة "قراءة الملف..."  
    sent_msg = bot.send_message(chat_id, "𝙿𝚕𝚎𝚊𝚜𝚎 𝚆𝚊𝚒𝚝 𝙲𝚑𝚎𝚌𝚔𝚒𝚗𝚐 𝚢𝚘𝚞𝚛 𝙲𝚊𝚛𝚍...⌛")  
  
    time.sleep(0.1)  
    bot.delete_message(chat_id, sent_msg.message_id)  
  
    # إرسال رسالة الفحص  
    processing_msg = bot.send_message(chat_id, "🔍 Checking …")  
  
    bins = load_bins()  
  
    approved_count = 0  
    dead_count = 0  
  
    # بدأ الفحص  
    for card in cards:  
        if stop_checking[chat_id]:  # إذا تم الضغط على زر STOP 🚧  
            break  
  
        time.sleep(random.randint(2, 3))  # تأخير بين كل فحص  
        if validate_card(card, bins):  
            approved_count += 1  
        else:  
            dead_count += 1  
  
        # تحديث الأزرار الشفافة مع البطاقة الحالية  
        markup = InlineKeyboardMarkup(row_width=1)  
        markup.add(  
            InlineKeyboardButton(f" {card}", callback_data='current_card'),  
            InlineKeyboardButton(f"☑️ 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝: {approved_count}", callback_data='approved'),  
            InlineKeyboardButton(f"⛔ Dead: {dead_count}", callback_data='dead'),  
            InlineKeyboardButton(f"⭐ Total: {total_count}", callback_data='total'),  
            InlineKeyboardButton("🚧 STOP", callback_data='stop')  
        )  
  
        # تحديث الرسالة كل ثانية  
        bot.edit_message_text("The examination has started 🔋 please wait … You are subscribed to VIP 🧾 Checking now, wait … ", chat_id, processing_msg.message_id, reply_markup=markup)  
        time.sleep(0.01)  
  
    # إذا تم الضغط على STOP  
    if stop_checking[chat_id]:  
        final_msg = "🛑\n\n"  
    else:  
        final_msg = "✅\n\n"  
  
    final_msg += f"☑️ Approved: {approved_count}\n⛔ Dead: {dead_count}\n⭐ Total: {total_count}"  
  
    # إرسال النتيجة النهائية  
    markup = InlineKeyboardMarkup(row_width=1)  
    markup.add(  
        InlineKeyboardButton(f"☑️ 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝: {approved_count}", callback_data='approved'),  
        InlineKeyboardButton(f"⛔ Dead: {dead_count}", callback_data='dead'),  
        InlineKeyboardButton(f"⭐ Total: {total_count}", callback_data='total')  
    )  
    bot.edit_message_text(final_msg, chat_id, processing_msg.message_id, reply_markup=markup)  
  
@bot.pre_checkout_query_handler(func=lambda query: True)  
def checkout_handler(pre_checkout_query: PreCheckoutQuery):  
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)  
  
@bot.message_handler(content_types=['successful_payment'])  
def successful_payment_handler(message):  
    chat_id = message.chat.id  
    user_id = message.from_user.id  
  
    # تخزين تاريخ انتهاء الاشتراك للمستخدم  
    vip_data = load_vip_data()  
    expire_time = datetime.now() + timedelta(days=1)  
    vip_data[str(user_id)] = expire_time.strftime('%Y-%m-%d %H:%M:%S')  
  
    update_vip_data(vip_data)  
  
    # بدء الفحص بعد الدفع الناجح  
    start_card_check(chat_id)  
  
    bot.send_message(chat_id, "تم الدفع بنجاح! شكرًا لشرائك. أنت الآن مشترك في خطة VIP لمدة يوم واحد. ⚡")  
  
@bot.callback_query_handler(func=lambda call: call.data == 'stop')  
def stop_processing(call):  
    global stop_checking  
    chat_id = call.message.chat.id  
    stop_checking[chat_id] = True  
    bot.answer_callback_query(call.id, "🛑")  
def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# حفظ البيانات إلى الملف
def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# إنشاء كود عشوائي
def generate_code():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=12))

# تحميل البيانات
vip_data = load_json(VIP_FILE)
codes_data = load_json(CODES_FILE)

# أمر /c لإنشاء كود
@bot.message_handler(commands=['c'])
def create_code(message):
    if message.from_user.id not in ADMINS:
        bot.reply_to(message, "❌ 𝒀𝒐𝒖 𝒅𝒐 𝒏𝒐𝒕 𝒉𝒂𝒗𝒆 𝒑𝒆𝒓𝒎𝒊𝒔𝒔𝒊𝒐𝒏.")
        return

    msg = bot.reply_to(message, "📌 𝑬𝒏𝒕𝒆𝒓 𝒕𝒉𝒆 𝒏𝒖𝒎𝒃𝒆𝒓 𝒐𝒇 𝒖𝒔𝒆𝒓𝒔 𝒂𝒍𝒍𝒐𝒘𝒆𝒅 𝒑𝒆𝒓 𝒄𝒐𝒅𝒆:")
    bot.register_next_step_handler(msg, process_user_count)

def process_user_count(message):
    try:
        max_users = int(message.text)
        msg = bot.reply_to(message, "⏳ 𝑬𝒏𝒕𝒆𝒓 𝒔𝒖𝒃𝒔𝒄𝒓𝒊𝒑𝒕𝒊𝒐𝒏 𝒕𝒊𝒎𝒆 (𝐇𝐇:𝐌𝐌):")
        bot.register_next_step_handler(msg, lambda m: process_subscription_time(m, max_users))
    except ValueError:
        bot.reply_to(message, "❌ 𝑰𝒏𝒗𝒂𝒍𝒊𝒅 𝒏𝒖𝒎𝒃𝒆𝒓.")

def process_subscription_time(message, max_users):
    try:
        time_parts = message.text.split(":")
        if len(time_parts) != 2:
            raise ValueError
        
        hours, minutes = map(int, time_parts)
        duration = f"{hours:02}:{minutes:02}"  # حفظ فقط HH:MM

        code = generate_code()
        codes_data[code] = {"max_users": max_users, "used_users": [], "duration": duration}

        save_json(CODES_FILE, codes_data)

        bot.reply_to(message, f"✅ 𝑪𝒐𝒅𝒆 𝒄𝒓𝒆𝒂𝒕𝒆𝒅 𝒔𝒖𝒄𝒄𝒆𝒔𝒔𝒇𝒖𝒍𝒍𝒚:\n`{code}`", parse_mode="Markdown")
    except ValueError:
        bot.reply_to(message, "❌ 𝑬𝒏𝒕𝒆𝒓 𝒕𝒊𝒎𝒆 𝒊𝒏 𝒇𝒐𝒓𝒎𝒂𝒕 𝐇𝐇:𝐌𝐌.")

# أمر /reedem لتفعيل الكود
@bot.message_handler(commands=['reedem'])
def redeem_code(message):
    user_id = str(message.from_user.id)
    args = message.text.split()
    
    if len(args) != 2:
        bot.reply_to(message, "❌ 𝑪𝒐𝒓𝒓𝒆𝒄𝒕 𝒖𝒔𝒂𝒈𝒆:\n`/reedem <code>`", parse_mode="Markdown")
        return
    
    code = args[1]
    
    if code not in codes_data:
        bot.reply_to(message, "📛 𝑰𝒏𝒗𝒂𝒍𝒊𝒅 𝒄𝒐𝒅𝒆.")
        return
    
    code_info = codes_data[code]

    if user_id in code_info["used_users"]:
        bot.reply_to(message, "📛 𝑰 𝒖𝒔𝒆𝒅 𝒕𝒉𝒆 𝒎𝒂𝒙𝒊𝒎𝒖𝒎 𝒐𝒏 𝒆𝒂𝒄𝒉 𝒂𝒄𝒄𝒐𝒖𝒏𝒕, 𝒕𝒓𝒚 𝒐𝒏 𝒂𝒏𝒐𝒕𝒉𝒆𝒓 𝒂𝒄𝒄𝒐𝒖𝒏𝒕.")
        return
    
    if len(code_info["used_users"]) >= code_info["max_users"]:
        bot.reply_to(message, "📛 𝑻𝒉𝒆 𝒄𝒐𝒅𝒆 𝒉𝒂𝒔 𝒆𝒙𝒑𝒊𝒓𝒆𝒅.")
        return
    
    # الحصول على مدة الاشتراك الأصلية
    duration = code_info["duration"]

    # حساب وقت الانتهاء
    try:
        hours, minutes = map(int, duration.split(":"))
        expiry_time = datetime.now() + timedelta(hours=hours, minutes=minutes)
    except ValueError:
        bot.reply_to(message, "❌ 𝑬𝒓𝒓𝒐𝒓 𝒑𝒓𝒐𝒄𝒆𝒔𝒔𝒊𝒏𝒈 𝒕𝒉𝒆 𝒄𝒐𝒅𝒆.")
        return

    # إضافة المستخدم إلى قائمة المستخدمين المستفيدين
    code_info["used_users"].append(user_id)
    vip_data[user_id] = expiry_time.strftime("%Y-%m-%d %H:%M:%S")

    save_json(CODES_FILE, codes_data)
    save_json(VIP_FILE, vip_data)

    bot.reply_to(message, f"🎁 𝑻𝒉𝒆 𝒄𝒐𝒅𝒆 𝒉𝒂𝒔 𝒃𝒆𝒆𝒏 𝒔𝒖𝒄𝒄𝒆𝒔𝒔𝒇𝒖𝒍𝒍𝒚 𝒓𝒆𝒅𝒆𝒆𝒎𝒆𝒅!\n\n"
                          f"☞ 𝑵𝒖𝒎𝒃𝒆𝒓 𝒐𝒇 𝒑𝒆𝒐𝒑𝒍𝒆 𝒓𝒆𝒎𝒂𝒊𝒏𝒊𝒏𝒈: {code_info['max_users'] - len(code_info['used_users'])}\n"
                          f"⌚ 𝑨𝒅𝒅𝒆𝒅 𝒕𝒊𝒎𝒆: {duration}")

with open("flags.json", "r", encoding="utf-8") as f:
    country_flags = json.load(f)

# رابط الصورة
paypal_image = "https://imageshack.com/i/pm6peM5Rj"

fake = Faker()
Faker.seed(0)

# استبعاد إسرائيل من قائمة الدول
excluded_countries = {"Israel", "IL"}

@bot.message_handler(commands=['paypal'])
def send_fake_identity(message):
    while True:
        country_name = fake.country()
        
        if country_name not in excluded_countries:
            break

    # محاولة الحصول على رمز الدولة الصحيح باستخدام pycountry
    try:
        country_obj = pycountry.countries.lookup(country_name)
        country_code = country_obj.alpha_2  # استخراج رمز الدولة
    except LookupError:
        country_code = None  # إذا لم يُعثر عليها، استخدم علم افتراضي

    country_flag = country_flags.get(country_code, "🏳️") if country_code else "🏳️"

    address = fake.address().replace("\n", ", ")  
    response = f"""
*𝗙𝘂𝗹𝗹 𝗡𝗮𝗺𝗲 𝟭:* `{fake.name()}`
*📧 𝗘𝗺𝗮𝗶𝗹:* `{fake.email()}`
*📞 𝗣𝗵𝗼𝗻𝗲 𝗡𝘂𝗺𝗯𝗲𝗿:* `{fake.phone_number()}`
*🏠 𝗔𝗱𝗱𝗿𝗲𝘀𝘀:* `{address}`
*𝗖𝗼𝘂𝗻𝘁𝗿𝘆🔎:* `{country_name}` {country_flag}
"""
    bot.send_photo(message.chat.id, paypal_image, caption=emoji.emojize(response, language="alias"), parse_mode="Markdown")

while True:  
    try: bot.polling(none_stop=True, interval=0)  
    except Exception as e: time.sleep(5)
