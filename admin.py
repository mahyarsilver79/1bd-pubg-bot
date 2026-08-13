import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import create_match


def is_admin(user_id):
    admin_id = os.getenv("ADMIN_ID")

    if not admin_id:
        return False

    return str(user_id) == str(admin_id)


def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 مسابقات", callback_data="adm_matches")],
        [InlineKeyboardButton("🏠 روم‌ها", callback_data="adm_rooms")],
        [InlineKeyboardButton("👥 بازیکنان", callback_data="adm_players")],
        [InlineKeyboardButton("💰 کیف پول", callback_data="adm_wallets")],
        [InlineKeyboardButton("📊 آمار", callback_data="adm_stats")],
    ])


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ دسترسی غیرمجاز.")
        return

    context.user_data.clear()

    await update.message.reply_text(
        "👑 پنل مدیریت 1BD PUBG\n\n"
        "یک بخش را انتخاب کن:",
        reply_markup=admin_menu()
    )


async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("⛔ دسترسی غیرمجاز.")
        return

    if query.data == "adm_matches":

        await query.edit_message_text(
            "🎮 مدیریت مسابقات",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "➕ ساخت مسابقه",
                        callback_data="adm_create_match"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="adm_back"
                    )
                ]
            ])
        )

    elif query.data == "adm_create_match":

        context.user_data.clear()
        context.user_data["admin_state"] = "waiting_match_name"

        await query.edit_message_text(
            "🎮 ساخت مسابقه\n\n"
            "اسم مسابقه را بفرست:\n\n"
            "اسم کاملاً آزاده؛ مثلاً:\n"
            "• 1\n"
            "• مسابقه جمعه\n"
            "• PUBG NIGHT 01\n"
            "• هر اسمی که خواستی"
        )

    elif query.data == "adm_back":

        context.user_data.clear()

        await query.edit_message_text(
            "👑 پنل مدیریت 1BD PUBG\n\n"
            "یک بخش را انتخاب کن:",
            reply_markup=admin_menu()
        )

    elif query.data == "adm_rooms":

        await query.edit_message_text(
            "🏠 مدیریت روم‌ها\n\n"
            "این بخش را بعد از ساخت مسابقه فعال می‌کنیم.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="adm_back"
                    )
                ]
            ])
        )

    elif query.data == "adm_players":

        await query.edit_message_text(
            "👥 مدیریت بازیکنان\n\n"
            "به‌زودی.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="adm_back"
                    )
                ]
            ])
        )

    elif query.data == "adm_wallets":

        await query.edit_message_text(
            "💰 مدیریت کیف پول\n\n"
            "به‌زودی.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="adm_back"
                    )
                ]
            ])
        )

    elif query.data == "adm_stats":

        await query.edit_message_text(
            "📊 آمار\n\n"
            "به‌زودی.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="adm_back"
                    )
                ]
            ])
        )


async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return False

    state = context.user_data.get("admin_state")

    if state != "waiting_match_name":
        return False

    name = update.message.text

    if not name:
        await update.message.reply_text(
            "❌ اسم مسابقه نمی‌تواند خالی باشد."
        )
        return True

    name = name.strip()

    try:

        match_id = create_match(name)

        context.user_data.clear()

        await update.message.reply_text(
            "✅ مسابقه با موفقیت ساخته شد!\n\n"
            f"🎮 نام مسابقه:\n{name}\n\n"
            f"🆔 ID مسابقه: {match_id}\n\n"
            "حالا می‌تونیم روم‌های این مسابقه رو بسازیم.",
            reply_markup=admin_menu()
        )

    except Exception as error:

        print("ADMIN CREATE MATCH ERROR:", repr(error))

        await update.message.reply_text(
            "❌ هنگام ساخت مسابقه خطایی رخ داد.\n\n"
            "جزئیات خطا در Logs ثبت شد."
        )

    return True
