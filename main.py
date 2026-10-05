import logging
import json
import re
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Configuration Setup
TOKEN = '8854896234:AAFvwhgwe5AorYDt8kAkNvPOcJwakrxbZ9Q'
ADMIN_ID = 8935181146
GEMINI_API_KEY = 'AQ.Ab8RN6Kuz6k0GfcaRuJRarQb-0SZx4w9jjNQ03tVNTVcXIkSA'

ai_client = genai.Client(api_key=GEMINI_API_KEY)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

user_balances = {}
pending_keys = {} # Store user ID for pending key delivery

def get_user_balance(user_id):
    if user_id not in user_balances:
        user_balances[user_id] = {'BDT': 0.0, 'INR': 0.0}
    return user_balances[user_id]

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    bal = get_user_balance(user_id)
    
    keyboard = [
        [InlineKeyboardButton("💰 My Wallet / ব্যালেন্স", callback_data='my_wallet'), InlineKeyboardButton("➕ Add Balance", callback_data='add_balance_menu')],
        [InlineKeyboardButton("🛍 AIM HACK", callback_data='aim_hack'), InlineKeyboardButton("🛍️ BALA MOD", callback_data='bala_mod')],
        [InlineKeyboardButton("🛍️ DRIP WIRE", callback_data='drip_wire'), InlineKeyboardButton("🛍 HG CHEATS", callback_data='hg_cheats')],
        [InlineKeyboardButton("🛍 PRIME HOOK", callback_data='prime_hook'), InlineKeyboardButton("🛍 XYZ CHEATS", callback_data='xyz_cheats')],
        [InlineKeyboardButton("🛍 Z REX", callback_data='z_rex')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = (
        f"🛍 **SOHAN VIP SHOP**\n\n"
        f"👤 **Your Account:** `{update.effective_user.full_name}`\n"
        f"💵 **Balance:** `{round(bal['BDT'], 2)} BDT` | `{round(bal['INR'], 2)} INR`\n\n"
        f"Please select an option below:"
    )
    if update.message:
        await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(msg, parse_mode='Markdown', reply_markup=reply_markup)

# Callback Click Handlers
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == 'main_menu':
        await start(update, context)
        return

    if data == 'my_wallet':
        bal = get_user_balance(user_id)
        w_msg = (
            f"💳 **YOUR WALLET DETAILS**\n\n"
            f"👤 **User:** {query.from_user.full_name}\n"
            f"🆔 **ID:** `{user_id}`\n\n"
            f"🇧🇩 **BDT Balance:** `{round(bal['BDT'], 2)} ৳`\n"
            f"🇮🇳 **INR Balance:** `{round(bal['INR'], 2)} ₹`\n"
        )
        kb = [
            [InlineKeyboardButton("➕ Add Balance", callback_data='add_balance_menu')],
            [InlineKeyboardButton("🔙 Main Menu", callback_data='main_menu')]
        ]
        await query.message.reply_text(w_msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == 'add_balance_menu':
        kb = [
            [InlineKeyboardButton("🇧🇩 Add BDT (Bkash/Nagad)", callback_data='select_country_BD'), InlineKeyboardButton("🇮🇳 Add INR (PhonePe/UPI)", callback_data='select_country_IN')],
            [InlineKeyboardButton("🔙 Main Menu", callback_data='main_menu')]
        ]
        await query.message.reply_text("🌐 **Select Payment Currency / কারেন্সি সিলেক্ট করুন:**", reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("select_country_"):
        country = data.split("_")[2]
        context.user_data['country'] = country
        currency = "BDT (৳)" if country == "BD" else "INR (₹)"
        
        amounts = [50, 100, 200, 500, 1000, 2000]
        kb = []
        for i in range(0, len(amounts), 2):
            btn1 = InlineKeyboardButton(f"{amounts[i]} {currency}", callback_data=f"amt_{amounts[i]}")
            btn2 = InlineKeyboardButton(f"{amounts[i+1]} {currency}", callback_data=f"amt_{amounts[i+1]}")
            kb.append([btn1, btn2])
        
        kb.append([InlineKeyboardButton("🔙 Back / পেছনে যান", callback_data='add_balance_menu')])
        
        amt_text = (
            f"💵 **Select Amount / টাকার পরিমাণ সিলেক্ট করুন ({currency}):**\n\n"
            f"আপনি কত টাকা/রুপি অ্যাড করতে চান নিচের বাটন থেকে সিলেক্ট করুন:"
        )
        await query.message.reply_text(amt_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("amt_"):
        selected_amount = float(data.split("_")[1])
        context.user_data['selected_amount'] = selected_amount
        context.user_data['is_direct_buy'] = False
        country = context.user_data.get('country', 'BD')

        if country == 'BD':
            bd_msg = (
                f"💳 **Add {selected_amount} BDT Balance (বাংলাদেশ):**\n\n"
                f"🔴 **নগদ (Send Money):** `01319098849`\n"
                f"💗 **বিকাশ (Personal):** `01757958863`\n\n"
                f"📌 **আপনার সিলেক্ট করা পরিমাণ:** `{selected_amount} ৳`\n"
                f"উপরের নম্বরগুলোতে **{selected_amount} ৳** পাঠিয়ে পেমেন্টের **Screenshot** পাঠান।"
            )
            kb = [[InlineKeyboardButton("🔙 Main Menu", callback_data='main_menu')]]
            await query.message.reply_text(bd_msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
        else:
            in_msg = (
                f"🇮🇳 **Add {selected_amount} INR Balance (India Payment):**\n\n"
                f"👤 **Name:** KARIMA BIBI\n"
                f"🆔 **UPI ID:** `9679798814@axl`\n\n"
                f"📌 **Selected Amount:** `{selected_amount} ₹`\n"
                f"📲 **Scan the QR Code to pay {selected_amount} INR.**\n"
                f"After payment, please send the **Payment Screenshot**."
            )
            kb = [[InlineKeyboardButton("🔙 Main Menu", callback_data='main_menu')]]
            direct_qr_url = "https://i.postimg.cc/hvsdkGwd/IMG-20260926-171136-047.jpg"
            
            try:
                await query.message.reply_photo(photo=direct_qr_url, caption=in_msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
            except Exception:
                await query.message.reply_text(in_msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
        return

    # Approve for Wallet Balance
    if data.startswith("app_wallet_"):
        parts = data.split("_")
        target_user_id = int(parts[2])
        amount = float(parts[3])
        currency = parts[4]

        bal = get_user_balance(target_user_id)
        bal[currency] += amount
        approve_text = f"🎉 **পেমেন্ট সফল হয়েছে!**\n\nআপনার ওয়ালেটে **{amount} {currency}** যোগ করা হয়েছে। বর্তমান ব্যালেন্স: `{round(bal[currency], 2)} {currency}`"

        user_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛍️ Main Menu", callback_data='main_menu')]])
        try:
            await context.bot.send_message(chat_id=target_user_id, text=approve_text, parse_mode='Markdown', reply_markup=user_kb)
        except Exception as e:
            logging.error(f"Failed msg: {e}")

        status_msg = f"\n\n✅ **APPROVED ({amount} {currency} Added)**"
        if query.message.caption:
            await query.edit_message_caption(caption=query.message.caption + status_msg, parse_mode='Markdown')
        else:
            await query.edit_message_text(text=query.message.text + status_msg, parse_mode='Markdown')
        return

    # Prompt Admin to send Key for Direct Order
    if data.startswith("app_direct_"):
        parts = data.split("_")
        target_user_id = int(parts[2])
        pkg_name = parts[3]
        
        pending_keys[user_id] = target_user_id
        prompt_msg = (
            f"🔑 **আপনার কাঙ্ক্ষিত Key-টি মেসেজে লিখে পাঠান:**\n\n"
            f"ইউজার ID: `{target_user_id}`\n"
            f"প্রোডাক্ট: `{pkg_name}`\n\n"
            f"*(শুধু Key বা ডাউনলোড লিঙ্ক লিখে সেন্ড করুন, ইউজারের কাছে সরাসরি চলে যাবে)*"
        )
        await query.message.reply_text(prompt_msg, parse_mode='Markdown')
        return

    if data.startswith("rej_"):
        target_user_id = int(data.split("_")[1])
        reject_text = "❌ **Payment Verification Failed!**\n\nYour submitted payment proof was invalid or fake. Please send a valid screenshot."
        user_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Main Menu", callback_data='main_menu')]])
        
        try:
            await context.bot.send_message(chat_id=target_user_id, text=reject_text, parse_mode='Markdown', reply_markup=user_kb)
        except Exception as e:
            logging.error(f"Failed msg: {e}")

        status_msg = "\n\n❌ **REJECTED BY ADMIN**"
        if query.message.caption:
            await query.edit_message_caption(caption=query.message.caption + status_msg, parse_mode='Markdown')
        else:
            await query.edit_message_text(text=query.message.text + status_msg, parse_mode='Markdown')
        return

    if data.startswith("pkg_"):
        raw_info = data.replace("pkg_", "")
        pkg_name, price_str = raw_info.split("|")
        price = float(price_str)
        
        context.user_data['pkg_name'] = pkg_name
        context.user_data['pkg_price'] = price
        bal = get_user_balance(user_id)
        
        country_msg = (
            f"🛒 **Selected Package:** `{pkg_name}`\n"
            f"💰 **Price:** `{price} BDT / INR`\n\n"
            f"💳 **Your Balance:** `{round(bal['BDT'], 2)} BDT` | `{round(bal['INR'], 2)} INR`\n\n"
            f"পেমেন্ট এর মাধ্যম নির্বাচন করুন:"
        )
        kb = [
            [InlineKeyboardButton("🇧🇩 Direct Pay (Bkash/Nagad)", callback_data='pay_direct_BD'), InlineKeyboardButton("🇮🇳 Direct Pay (PhonePe/UPI)", callback_data='pay_direct_IN')],
            [InlineKeyboardButton("💰 Buy with BDT Balance", callback_data='buy_wallet_BDT'), InlineKeyboardButton("💰 Buy with INR Balance", callback_data='buy_wallet_INR')],
            [InlineKeyboardButton("🔙 Main Menu", callback_data='main_menu')]
        ]
        await query.message.reply_text(country_msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("pay_direct_"):
        country = data.split("_")[2]
        pkg_name = context.user_data.get('pkg_name', 'Package')
        price = context.user_data.get('pkg_price', 0.0)
        
        context.user_data['country'] = country
        context.user_data['selected_amount'] = price
        context.user_data['is_direct_buy'] = True

        if country == 'BD':
            bd_msg = (
                f"🛒 **Buy Package:** `{pkg_name}`\n"
                f"💰 **Amount to Pay:** `{price} ৳`\n\n"
                f"🔴 **নগদ (Send Money):** `01319098849`\n"
                f"💗 **বিকাশ (Personal):** `01757958863`\n\n"
                f"উপরের নম্বরগুলোতে **{price} ৳** পাঠিয় পেমেন্টের **Screenshot** পাঠান।"
            )
            kb = [[InlineKeyboardButton("🔙 Main Menu", callback_data='main_menu')]]
            await query.message.reply_text(bd_msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
        else:
            in_msg = (
                f"🛒 **Buy Package:** `{pkg_name}`\n"
                f"💰 **Amount to Pay:** `{price} ₹`\n\n"
                f"👤 **Name:** KARIMA BIBI\n"
                f"🆔 **UPI ID:** `9679798814@axl`\n\n"
                f"Scan QR or pay **{price} INR** to UPI ID. Then send the **Payment Screenshot**."
            )
            kb = [[InlineKeyboardButton("🔙 Main Menu", callback_data='main_menu')]]
            direct_qr_url = "https://i.postimg.cc/hvsdkGwd/IMG-20260926-171136-047.jpg"
            try:
                await query.message.reply_photo(photo=direct_qr_url, caption=in_msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
            except Exception:
                await query.message.reply_text(in_msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("buy_wallet_"):
        currency = data.split("_")[2]
        pkg_name = context.user_data.get('pkg_name', 'Product')
        price = context.user_data.get('pkg_price', 0.0)
        bal = get_user_balance(user_id)

        if bal[currency] >= price:
            bal[currency] -= price
            success_msg = (
                f"✅ **অর্ডার সফল হয়েছে!**\n\n"
                f"📦 **Product:** `{pkg_name}`\n"
                f"💸 **Paid:** `{price} {currency}`\n"
                f"💰 **Remaining Balance:** `{round(bal[currency], 2)} {currency}`\n\n"
                f"⏳ **অ্যাডমিন আপনার কী (Key) জেনারেট করছেন। কিছুক্ষণের মধ্যেই বট আপনাকে Key টি পাঠাবে!**"
            )
            kb = [[InlineKeyboardButton("🛍 Main Menu", callback_data='main_menu')]]
            await query.message.reply_text(success_msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
            
            admin_noti = (
                f"🛍️️ **NEW WALLET ORDER RECEIVED!**\n\n"
                f"👤 **User:** {query.from_user.full_name} (@{query.from_user.username})\n"
                f"🆔 **ID:** `{user_id}`\n"
                f"📦 **Product:** `{pkg_name}`\n"
                f"💵 **Paid:** `{price} {currency}`\n\n"
                f"📌 **ইউজারকে Key পাঠাতে এটি কপি করুন:**\n"
                f"`/sendkey {user_id} আপনার_কী_এখানে_লিখুন`"
            )
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_noti, parse_mode='Markdown')
        else:
            fail_msg = (
                f"❌ **Insufficient Balance!**\n\n"
                f"আপনার ওয়ালেটে পর্যাপ্ত **{currency}** ব্যালেন্স নেই।\n"
                f"প্রয়োজন: `{price} {currency}`\n"
                f"বর্তমান ব্যালেন্স: `{round(bal[currency], 2)} {currency}`\n\n"
                f"আপনি সরাসরি বিকাশ/নগদ/UPI দিয়েও অর্ডার করতে পারেন।"
            )
            kb = [
                [InlineKeyboardButton("➕ Add Balance", callback_data='add_balance_menu')],
                [InlineKeyboardButton("🔙 Main Menu", callback_data='main_menu')]
            ]
            await query.message.reply_text(fail_msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
        return

    # Packages List
    packages = []
    title = ""

    if data == 'z_rex':
        title = "Z REX - NON ROOT"
        packages = [("Zrex 1 Days - ৳80", "pkg_Zrex 1 Day|80"), ("Zrex 3 Days - ৳180", "pkg_Zrex 3 Days|180"), ("Zrex 7 Days - ৳350", "pkg_Zrex 7 Days|350")]
    elif data == 'xyz_cheats':
        title = "XYZ CHEATS - NON ROOT"
        packages = [("xyz 1 hour - ৳20", "pkg_XYZ 1h|20"), ("xyz 2 hour - ৳40", "pkg_XYZ 2h|40"), ("xyz 4 hour - ৳65", "pkg_XYZ 4h|65"), ("xyz 6 hour - ৳90", "pkg_XYZ 6h|90"), ("xyz 12 hour - ৳160", "pkg_XYZ 12h|160"), ("xyz 1 day - ৳200", "pkg_XYZ 1d|200"), ("xyz 3 day - ৳400", "pkg_XYZ 3d|400"), ("xyz 7 day - ৳700", "pkg_XYZ 7d|700"), ("xyz 30 day - ৳1450", "pkg_XYZ 30d|1450")]
    elif data == 'prime_hook':
        title = "PRIME HOOK - NON ROOT"
        packages = [("Prime 1 Days - ৳60", "pkg_Prime 1d|60"), ("Prime 3 Days - ৳150", "pkg_Prime 3d|150"), ("Prime 7 Days - ৳300", "pkg_Prime 7d|300")]
    elif data == 'hg_cheats':
        title = "HG CHEATS - NON ROOT"
        packages = [("Hg Cheats 1 days - ৳80", "pkg_HG 1d|80"), ("Hg Cheats 7 days - ৳250", "pkg_HG 7d|250"), ("Hg Cheats 10 days - ৳300", "pkg_HG 10d|300"), ("Hg Cheats 30 days - ৳650", "pkg_HG 30d|650")]
    elif data == 'aim_hack':
        title = "AIM HACK - NON ROOT"
        packages = [("1 hour - ৳20", "pkg_AIM 1h|20"), ("3 hour - ৳40", "pkg_AIM 3h|40"), ("6 hour - ৳60", "pkg_AIM 6h|60"), ("12 hour - ৳90", "pkg_AIM 12h|90"), ("1 day - ৳130", "pkg_AIM 1d|130"), ("3 day - ৳250", "pkg_AIM 3d|250"), ("7 day - ৳400", "pkg_AIM 7d|400"), ("30 day - ৳1100", "pkg_AIM 30d|1100")]
    elif data == 'bala_mod':
        title = "BALA MOD - NON ROOT"
        packages = [("1 hour - ৳20", "pkg_Bala 1h|20"), ("2 hour - ৳40", "pkg_Bala 2h|40"), ("3 hour - ৳60", "pkg_Bala 3h|60"), ("4 hour - ৳70", "pkg_Bala 4h|70"), ("5 hour - ৳80", "pkg_Bala 5h|80"), ("6 hour - ৳90", "pkg_Bala 6h|90"), ("7 hour - ৳100", "pkg_Bala 7h|100"), ("8 hour - ৳110", "pkg_Bala 8h|110"), ("9 hour - ৳120", "pkg_Bala 120"), ("10 hour - ৳130", "pkg_Bala 10h|130"), ("1 day - ৳280", "pkg_Bala 1d|280"), ("2 day - ৳550", "pkg_Bala 2d|550"), ("3 day - ৳750", "pkg_Bala 3d|750"), ("7 day - ৳1750", "pkg_Bala 7d|1750"), ("30 day - ৳7200", "pkg_Bala 30d|7200")]
    elif data == 'drip_wire':
        title = "DRIP WIRE - NON ROOT"
        packages = [("Wire 6 hour - ৳48", "pkg_Wire 6h|48"), ("Wire 12 hour - ৳75", "pkg_Wire 12h|75"), ("Wire 1 day - ৳120", "pkg_Wire 1d|120"), ("Wire 7 day - ৳450", "pkg_Wire 7d|450"), ("Wire 30 day - ৳1100", "pkg_Wire 30d|1100")]

    keyboard = []
    for i in range(0, len(packages), 2):
        row = [InlineKeyboardButton(packages[i][0], callback_data=packages[i][1])]
        if i + 1 < len(packages):
            row.append(InlineKeyboardButton(packages[i+1][0], callback_data=packages[i+1][1]))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data='main_menu')])
    await query.message.reply_text(f"📦 **{title}**\n\nSelect a package:", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def send_key_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        user_id = int(context.args[0])
        key_text = " ".join(context.args[1:])

        key_msg = (
            f"🎉 **YOUR LICENSE KEY & APP LINK!**\n\n"
            f"🔑 **Key/Link Details:**\n`{key_text}`\n\n"
            f"ধন্যবাদ আমাদের সাথে থাকার জন্য! ❤️"
        )
        
        await context.bot.send_message(chat_id=user_id, text=key_msg, parse_mode='Markdown')
        await update.message.reply_text(f"✅ **User ID `{user_id}` কে সফলভাবে Key পাঠানো হয়েছে!**", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text("❌ **ভুল ফরম্যাট!** এভাবে লিখুন:\n`/sendkey USER_ID আপনার_কী`", parse_mode='Markdown')

# Strict Payment Verification
async def verify_payment_with_ai(country, image_bytes=None, text_proof=None):
    if text_proof:
        # Check if text looks like random garbage or less than 8 characters
        if len(text_proof.strip()) < 8 or not re.search(r'\d', text_proof):
            return False
            
    prompt = f"""
    You are an extremely strict AI Payment Verification Expert.
    Country Mode Selected: {country} (BD = Bangladesh, IN = India)

    STRICT RULES:
    1. Only approve if the photo is an EXACT payment screenshot from Bkash, Nagad, PhonePe, Paytm, or UPI.
    2. Reject all random photos, memes, selfies, or non-payment images.
    """
    
    try:
        contents = [prompt]
        if image_bytes:
            img = Image.open(BytesIO(image_bytes))
            contents.append(img)
        else:
            contents.append(f"User Text Proof: {text_proof}")

        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "is_valid": {"type": "BOOLEAN"}
                    },
                    "required": ["is_valid"]
                }
            )
        )
        res_data = json.loads(response.text)
        return res_data.get("is_valid", False)

    except Exception as e:
        logging.error(f"AI Error: {e}")
        return False

# Handle Input/Proof
async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    
    # Check if Admin is responding with a Key
    if user.id == ADMIN_ID and user.id in pending_keys:
        target_user_id = pending_keys.pop(user.id)
        key_text = update.message.text
        
        key_msg = (
            f"🎉 **YOUR LICENSE KEY & APP LINK!**\n\n"
            f"🔑 **Key/Link Details:**\n`{key_text}`\n\n"
            f"ধন্যবাদ আমাদের সাথে থাকার জন্য! ❤️"
        )
        try:
            await context.bot.send_message(chat_id=target_user_id, text=key_msg, parse_mode='Markdown')
            await update.message.reply_text(f"✅ **User ID `{target_user_id}` কে সফলভাবে Key পাঠানো হয়েছে!**", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ মেসেজ পাঠানো যায়নি: {e}")
        return

    if update.message.text and update.message.text.startswith('/'):
        return

    user_country = context.user_data.get('country', 'BD')
    amount = context.user_data.get('selected_amount', 100.0)
    is_direct_buy = context.user_data.get('is_direct_buy', False)
    pkg_name = context.user_data.get('pkg_name', 'Direct Purchase')
    currency = 'BDT' if user_country == 'BD' else 'INR'
    
    username_str = f"@{user.username}" if user.username else "No Username"
    text_input = update.message.text if update.message.text else "Photo Attachment"

    verifying_msg = await update.message.reply_text("🔍 **AI is verifying payment proof... Please wait.**")
    
    is_valid = False
    image_bytes = None

    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
        is_valid = await verify_payment_with_ai(country=user_country, image_bytes=image_bytes)
    else:
        is_valid = await verify_payment_with_ai(country=user_country, text_proof=update.message.text)

    await verifying_msg.delete()

    if not is_valid:
        error_msg = (
            "⚠️️ **Invalid Payment Proof!**\n\n"
            "আপনার পাঠানো ছবি বা টেক্সটটি সঠিক পেমেন্ট প্রুফ নয়।\n"
            "অনুগ্রহ করে বিকাশ, নগদ বা UPI-এর আসল **Payment Screenshot** পাঠান।"
        )
        user_cancel_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data='main_menu')]])
        await update.message.reply_text(error_msg, parse_mode='Markdown', reply_markup=user_cancel_kb)
        return

    if is_direct_buy:
        admin_msg = (
            f"🚨 **NEW DIRECT ORDER ({pkg_name})!**\n\n"
            f"👤 **User:** {user.full_name}\n"
            f"🏷 **Username:** {username_str}\n"
            f"🆔 **User ID:** `{user.id}`\n"
            f"💵 **Price:** `{amount} {currency}`\n\n"
            f"👇 **ইউজারকে Key পাঠাতে নিচের বাটনে চাপ দিন:**"
        )
        admin_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔑 Approve & Send Key", callback_data=f"app_direct_{user.id}_{pkg_name}")],
            [InlineKeyboardButton("❌ Reject Request", callback_data=f"rej_{user.id}")]
        ])
    else:
        admin_msg = (
            f"🚨 **NEW BALANCE ADD REQUEST!**\n\n"
            f"👤 **User:** {user.full_name}\n"
            f"🆔 **User ID:** `{user.id}`\n"
            f"💵 **Amount:** `{amount} {currency}`"
        )
        admin_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"✅ Approve ({amount} {currency})", callback_data=f"app_wallet_{user.id}_{amount}_{currency}")],
            [InlineKeyboardButton("❌ Reject Request", callback_data=f"rej_{user.id}")]
        ])
    
    if update.message.photo:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=admin_msg,
            parse_mode='Markdown',
            reply_markup=admin_markup
        )
    else:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_msg,
            parse_mode='Markdown',
            reply_markup=admin_markup
        )

    user_response = f"⏳ **Payment Proof Received!**\n\nAdmin will verify and send your Key shortly."
    user_cancel_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data='main_menu')]])

    await update.message.reply_text(user_response, parse_mode='Markdown', reply_markup=user_cancel_kb)

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("sendkey", send_key_command))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.PHOTO | filters.TEXT, handle_payment_proof))
    
    application.run_polling()

if __name__ == '__main__':
    main()

