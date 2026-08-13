import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎮 ثبت‌نام مسابقه", callback_data="register")],
        [InlineKeyboardButton("📋 مسابقات من", callback_data="my_matches")],
        [InlineKeyboardButton("💰 کیف پول", callback_data="wallet")],
        [InlineKeyboardButton("📜 قوانین", callback_data="rules")],
        [InlineKeyboardButton("🎧 پشتیبانی", callback_data="support")],
    ]

    await update.message.reply_text(
        "🎮 به ربات 1BD PUBG خوش اومدی!\n\n"
        "مسابقه موردنظرت رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "register":
        await query.edit_message_text(
            "🎮 ثبت‌نام مسابقه\n\n"
            "فعلاً هیچ رومی برای ثبت‌نام فعال نیست."
        )

    elif query.data == "my_matches":
        await query.edit_message_text(
            "📋 مسابقات من\n\n"
            "هنوز در هیچ مسابقه‌ای ثبت‌نام نکردی."
        )

    elif query.data == "wallet":
        await query.edit_message_text(
            "💰 کیف پول\n\n"
            "موجودی: ۰ تومان"
        )

    elif query.data == "rules":
        await query.edit_message_text(
            "📜 قوانین مسابقات\n\n"
            "قوانین مسابقه در این بخش نمایش داده می‌شود."
        )

    elif query.data == "support":
        await query.edit_message_text(
            "🎧 پشتیبانی\n\n"
            "برای ارتباط با پشتیبانی پیام ارسال کنید."
        )


def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN تنظیم نشده است.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 ربات 1BD اجرا شد...")
    app.run_polling()


if __name__ == "__main__":
    main()
