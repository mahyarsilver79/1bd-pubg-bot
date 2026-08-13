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
        [InlineKeyboardButton("🎮 ساخت مسابقه", callback_data="adm_create_match")],
        [InlineKeyboardButton("🏠 مدیریت روم‌ها", callback_data="adm_rooms")],
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
        "یک گزینه را انتخاب کن:",
        reply_markup=admin_menu()
    )


async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("⛔ دسترسی غیرمجاز.")
        return

    if query.data == "adm_create_match":

        context.user_data.clear()
        context.user_data["admin_state"] = "waiting_match_name"

        await query.edit_message_text(
            "🎮 ساخت مسابقه\n\n"
            "✏️ لطفاً اسم مسابقه را وارد کن:\n\n"
            "مثال:\n"
            "مسابقه جمعه شب\n"
            "یا حتی:\n"
            "1",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "❌ لغو",
                        callback_data="adm_cancel"
                    )
                ]
            ])
        )

    elif query.data == "adm_cancel":

        context.user_data.clear()

        await query.edit_message_text(
            "👑 پنل مدیریت",
            reply_markup=admin_menu()
        )

    elif query.data == "adm_rooms":

        await query.edit_message_text(
            "🏠 مدیریت روم‌ها\n\n"
            "این بخش بعد از ساخت مسابقه فعال می‌شود.",
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
            "👥 بازیکنان\n\n"
            "این بخش به‌زودی فعال می‌شود.",
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
            "💰 کیف پول\n\n"
            "این بخش به‌زودی فعال می‌شود.",
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
            "این بخش به‌زودی فعال می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="adm_back"
                    )
                ]
            ])
        )

    elif query.data == "adm_back":

        context.user_data.clear()

        await query.edit_message_text(
            "👑 پنل مدیریت 1BD PUBG\n\n"
            "یک گزینه را انتخاب کن:",
            reply_markup=admin_menu()
        )


async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return False

    if context.user_data.get("admin_state") != "waiting_match_name":
        return False

    name = update.message.text.strip()

    if not name:
        await update.message.reply_text(
            "❌ اسم مسابقه خالی است.\n"
            "لطفاً اسم مسابقه را وارد کن."
        )
        return True

    try:

        match_id = create_match(name)

        context.user_data.clear()

        await update.message.reply_text(
            "✅ مسابقه ساخته شد!\n\n"
            f"🎮 اسم مسابقه: {name}\n"
            f"🆔 شماره مسابقه: {match_id}",
            reply_markup=admin_menu()
        )

    except Exception as e:

        print("CREATE MATCH ERROR:", repr(e))

        await update.message.reply_text(
            "❌ ساخت مسابقه انجام نشد.\n"
            "Logs را بررسی کن."
        )

    return True
