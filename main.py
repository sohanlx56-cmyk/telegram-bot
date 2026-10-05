import logging
import re
from google import genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Configuration (আপনার সব আইডি ও টোকেন সেট করা হয়েছে)
BOT_TOKEN = "8735454318:AAG541sgaZrMIo7B2oUxGVEKybTnE_xmkk8"
ADMIN_ID = 8935181146
GEMINI_API_KEY = "AQ.Ab8RN6Kuz6k0GfcaRuJRarQb-0SZx4w9jjNQ03tVNTVcXIkSA"

# AI Client Setup
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# Start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **VIP Shop Bot-এ আপনাকে স্বাগতম!**\n\n"
        "আমাদের সার্ভিস বা প্রোডাক্ট কিনতে নিচের **'🛒 Buy Products'** বাটনে ক্লিক করুন।"
    )
    keyboard = [
        [InlineKeyboardButton("🛒 Buy Products", callback_data="buy_products")],
        [InlineKeyboardButton("📞 Support", callback_data="support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

# Callback Query Handler
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "buy_products":
        keyboard = [
            [InlineKeyboardButton("⚡ 1 Day Pass - 100 BDT / 80 INR", callback_data="pkg_1day")],
            [InlineKeyboardButton("🔥 7 Days Pass - 500 BDT / 400 INR", callback_data="pkg_7day")],
            [InlineKeyboardButton("👑 30 Days Pass - 1500 BDT / 1200 INR", callback_data="pkg_30day")],
            [InlineKeyboardButton("🔙 Back", callback_data="start_menu")]
        ]
        await query.edit_message_text("📦 **একটি প্যাকেজ নির্বাচন করুন:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("pkg_"):
        pkg_type = data.split("_")[1]
        context.user_data['selected_pkg'] = pkg_type
        
        keyboard = [
            [InlineKeyboardButton("🇧🇩 BDT (Bkash/Nagad)", callback_data="curr_BDT")],
            [InlineKeyboardButton("🇮🇳 INR (UPI/Paytm)", callback_data="curr_INR")],
            [InlineKeyboardButton("🔙 Back", callback_data="buy_products")]
        ]
        await query.edit_message_text("💳 **পেমেন্ট কারেন্সি সিলেক্ট করুন:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("curr_"):
        currency = data.split("_")[1]
        pkg_type = context.user_data.get('selected_pkg', '1day')
        
        prices = {
            "1day": {"BDT": "100 BDT", "INR": "80 INR"},
            "7day": {"BDT": "500 BDT", "INR": "400 INR"},
            "30day": {"BDT": "1500 BDT", "INR": "1200 INR"}
        }
        
        price = prices.get(pkg_type, {}).get(currency, "N/A")
        context.user_data['pending_order'] = {"pkg": pkg_type, "curr": currency, "price": price}

        payment_info = (
            f"🛒 **প্যাকেজ:** {pkg_type.upper()}\n"
            f"💰 **মূল্য:** {price}\n\n"
            "📌 **পেমেন্ট ইন্সট্রাকশন:**\n"
        )
        
        if currency == "BDT":
            payment_info += (
                "📱 **bKash / Nagad Personal:** `017XXXXXXXX`\n"
                "⚠️ **Send Money** করার পর সঠিক ট্রানজেকশন আইডি (TrxID) লিখে অথবা পেমেন্ট কনফার্মেশনের স্পষ্ট স্ক্রিনশট নিচে পাঠান।"
            )
        else:
            payment_info += (
                "📱 **UPI ID:** `yourupi@upi`\n"
                "⚠️ পেমেন্ট করার পর সফল পেমেন্টের স্ক্রিনশট বা UTR/TrxID পাঠান।"
            )

        context.user_data['awaiting_payment'] = True
        await query.edit_message_text(payment_info, parse_mode="Markdown")

    elif data == "start_menu":
        await start(update, context)

    # Admin Approvals
    elif data.startswith("approve_"):
        user_id = int(data.split("_")[1])
        await query.edit_message_text(f"✅ পেমেন্ট অ্যাপ্রুভ হয়েছে (User ID: `{user_id}`)।\n\nএখন কি/লিংক পাঠাতে টাইপ করুন:\n`/sendkey {user_id} আপনার_কি_বা_লিংক`", parse_mode="Markdown")
        await context.bot.send_message(chat_id=user_id, text="🎉 **আপনার পেমেন্ট ভেরিফাই করা হয়েছে!**\nঅ্যাডমিন খুব দ্রুত আপনাকে অ্যাক্সেস কি/লিংক পাঠিয়ে দিচ্ছে।")

    elif data.startswith("reject_"):
        user_id = int(data.split("_")[1])
        await query.edit_message_text(f"❌ অর্ডার রিজেক্ট করা হয়েছে (User ID: `{user_id}`)।", parse_mode="Markdown")
        await context.bot.send_message(chat_id=user_id, text="❌ **আপনার পেমেন্ট ভেরিফিকেশন বাতিল হয়েছে।** সঠিক পেমেন্ট প্রুফ বা ট্রানজেকশন আইডি দিয়ে আবার চেষ্টা করুন।")

# Message Handler with AI Vision & TrxID Checks
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_payment'):
        return

    user = update.effective_user
    order_info = context.user_data.get('pending_order', {})
    
    # 1. AI Image Verification
    if update.message.photo:
        status_msg = await update.message.reply_text("🔍 **এআই পেমেন্ট প্রুফ স্ক্যান করছে, অনুগ্রহ করে অপেক্ষা করুন...**")
        
        try:
            photo_file = await update.message.photo[-1].get_file()
            photo_bytes = await photo_file.download_as_bytearray()

            prompt = (
                "Analyze this image carefully. Is this a valid payment confirmation screenshot "
                "(like bKash, Nagad, Rocket, UPI, Paytm, GooglePay, PhonePe, or bank transaction receipt)? "
                "Respond with ONLY 'VALID' if it clearly shows a successful payment statement/receipt/screenshot. "
                "Respond with ONLY 'INVALID' if it is a camera photo of random objects, fake edit, or unrelated picture."
            )
            
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    prompt,
                    {"mime_type": "image/jpeg", "data": bytes(photo_bytes)}
                ]
            )

            result_text = response.text.strip().upper()

            if "VALID" in result_text:
                await status_msg.edit_text("✅ **পেমেন্ট প্রুফ সঠিক পাওয়া গেছে!** এটি অ্যাডমিনের নিকট ভেরিফিকেশনের জন্য পাঠানো হয়েছে।")
                context.user_data['awaiting_payment'] = False

                admin_text = (
                    f"🔔 **নতুন অর্ডারের পেমেন্ট প্রুফ (AI Verified)!**\n\n"
                    f"👤 **ইউজার:** {user.full_name} (@{user.username})\n"
                    f"🆔 **User ID:** `{user.id}`\n"
                    f"📦 **প্যাকেজ:** {order_info.get('pkg', 'N/A')}\n"
                    f"💰 **মূল্য:** {order_info.get('price', 'N/A')}\n"
                )
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}"),
                        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
                    ]
                ]
                await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=admin_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await status_msg.edit_text("❌ **ভুল পেমেন্ট প্রুফ!**\n\nআমাদের এআই সিস্টেমে এটি কোনো বৈধ পেমেন্ট স্ক্রিনশট হিসেবে গণ্য হয়নি। অনুগ্রহ করে আপনার আসল পেমেন্টের স্ক্রিনশটটি পাঠান।")

        except Exception as e:
            logging.error(f"AI Check Error: {e}")
            await status_msg.edit_text("⚠ ভেরিফিকেশনে সাময়িক সমস্যা হয়েছে। আপনার ফাইলটি সরাসরি অ্যাডমিনের কাছে পাঠানো হচ্ছে...")
            context.user_data['awaiting_payment'] = False

    # 2. Text TrxID Check
    elif update.message.text:
        text = update.message.text.strip()
        trx_pattern = r'^[A-Za-z0-9]{8,12}$'
        
        if re.match(trx_pattern, text) and not text.isdigit():
            context.user_data['awaiting_payment'] = False
            await update.message.reply_text("✅ **ট্রানজেকশন আইডি জমা নেওয়া হয়েছে!** অ্যাডমিন এটি ভেরিফাই করে আপনাকে প্রোডাক্ট ডেলিভারি করবে।")

            admin_text = (
                f"🔔 **নতুন ট্রানজেকশন আইডি এসেছে!**\n\n"
                f"👤 **ইউজার:** {user.full_name} (@{user.username})\n"
                f"🆔 **User ID:** `{user.id}`\n"
                f"📦 **প্যাকেজ:** {order_info.get('pkg', 'N/A')}\n"
                f"💰 **মূল্য:** {order_info.get('price', 'N/A')}\n"
                f"📝 **TrxID:** `{text}`"
            )
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
                ]
            ]
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text("❌ **অকার্যকর ট্রানজেকশন আইডি!**\n\nঅনুগ্রহ করে একটি সঠিক ও বৈধ Transaction ID (TrxID) পাঠান অথবা সরাসরি পেমেন্টের স্ক্রিনশটটি দিন।")

# Send Key Command
async def send_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        target_user_id = int(context.args[0])
        key_or_link = " ".join(context.args[1:])

        if not key_or_link:
            await update.message.reply_text("⚠️ নিয়ম: `/sendkey <USER_ID> <KEY_OR_LINK>`")
            return

        delivery_text = (
            f"🎁 **আপনার ক্রয়কৃত প্রোডাক্ট:**\n\n"
            f"🔑 **Key / Access Link:** `{key_or_link}`\n\n"
            f"আমাদের সাথে থাকার জন্য ধন্যবাদ!"
        )
        await context.bot.send_message(chat_id=target_user_id, text=delivery_text, parse_mode="Markdown")
        await update.message.reply_text(f"✅ User `{target_user_id}`-কে Key/Link পাঠানো সম্পন্ন হয়েছে।")

    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ নিয়ম: `/sendkey <USER_ID> <KEY_OR_LINK>`")

# Main Function
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sendkey", send_key))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
