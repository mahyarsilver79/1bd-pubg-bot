import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import create_match, get_matches


def is_admin(user_id):
    admin_id = os.getenv("ADMIN_ID")

    if not admin_id:
        return False

    return str(user_id) == str(admin_id)


def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 ساخت مسابقه", callback_data="adm_create_match")],
        [InlineKeyboardButton("🏠 ساخت روم", callback_data="adm_create_room")],
        [InlineKeyboardButton("📋 لیست مسابقات", callback_data="adm_matches")],
    ])


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ دسترسی غیرمجاز.")
        return

    context.user_data.clear()

    await update.message.reply_text(
        "سلام مهیار 👋\n\n"
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
            "✏️ اسم مسابقه را وارد کن:\n\n"
            "مثال:\n"
            "مسابقه جمعه شب\n"
            "PUBG NIGHT\n"
            "یا حتی فقط:\n"
            "1",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "❌ لغو",
                    callback_data="adm_cancel"
                )]
            ])
        )

    elif query.data == "adm_create_room":

        await query.edit_message_text(
            "🏠 ساخت روم\n\n"
            "ابتدا یک مسابقه بساز.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "🔙 پنل مدیریت",
                    callback_data="adm_back"
                )]
            ])
        )

    elif query.data == "adm_matches":

        matches = get_matches()

        if not matches:

            text = "📋 هنوز هیچ مسابقه‌ای ساخته نشده."

        else:

            text = "📋 مسابقات:\n\n"

            for match in matches:
                text += (
                    f"🎮 {match['name']}\n"
                    f"🆔 ID: {match['id']}\n\n"
                )

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "➕ ساخت مسابقه",
                    callback_data="adm_create_match"
                )],
                [InlineKeyboardButton(
                    "🔙 پنل مدیریت",
                    callback_data="adm_back"
                )]
            ])
        )

    elif query.data == "adm_cancel":

        context.user_data.clear()

        await query.edit_message_text(
            "👑 پنل مدیریت",
            reply_markup=admin_menu()
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

    state = context.user_data.get("admin_state")

    if state == "waiting_match_name":

        name = update.message.text.strip()

        if not name:

            await update.message.reply_text(
                "❌ اسم مسابقه نمی‌تواند خالی باشد."
            )

            return True

        try:

            match_id = create_match(name)

            context.user_data.clear()

            await update.message.reply_text(
                "✅ مسابقه ساخته شد!\n\n"
                f"🎮 اسم مسابقه: {name}\n"
                f"🆔 ID مسابقه: {match_id}\n\n"
                "حالا می‌توانیم روم‌های این مسابقه را بسازیم.",
                reply_markup=admin_menu()
            )

        except Exception as error:

            print("CREATE MATCH ERROR:", repr(error))

            await update.message.reply_text(
                "❌ خطا هنگام ساخت مسابقه.\n"
                "Logs را بررسی کن."
            )

        return True

    return False
