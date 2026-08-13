import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import create_match, create_room, get_connection


def is_admin(user_id):
    admin_id = os.getenv("ADMIN_ID")
    return admin_id and str(user_id) == str(admin_id)


def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 مسابقات", callback_data="adm_matches")],
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
        "یک بخش را انتخاب کن:",
        reply_markup=admin_menu()
    )


async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("⛔ دسترسی غیرمجاز.")
        return

    data = query.data

    if data == "adm_matches":
        await matches_menu(query)

    elif data == "adm_create_match":
        context.user_data.clear()
        context.user_data["admin_state"] = "waiting_match_name"

        await query.edit_message_text(
            "🎮 ساخت مسابقه\n\n"
            "اسم مسابقه را بفرست.\n\n"
            "می‌تونی هر چیزی بنویسی؛ فارسی، انگلیسی، عدد یا ترکیبی."
        )

    elif data == "adm_rooms":
        await rooms_menu(query)

    elif data == "adm_players":
        await query.edit_message_text(
            "👥 بازیکنان\n\n"
            "مدیریت بازیکنان در مرحله بعد اضافه می‌شود.",
            reply_markup=back_admin_button()
        )

    elif data == "adm_wallets":
        await query.edit_message_text(
            "💰 کیف پول‌ها\n\n"
            "مدیریت کیف پول در مرحله بعد اضافه می‌شود.",
            reply_markup=back_admin_button()
        )

    elif data == "adm_stats":
        await query.edit_message_text(
            "📊 آمار\n\n"
            "آمار مسابقات در مرحله بعد اضافه می‌شود.",
            reply_markup=back_admin_button()
        )

    elif data == "adm_back":
        await query.edit_message_text(
            "👑 پنل مدیریت 1BD PUBG\n\n"
            "یک بخش را انتخاب کن:",
            reply_markup=admin_menu()
        )

    elif data == "adm_cancel":
        context.user_data.clear()

        await query.edit_message_text(
            "❌ عملیات لغو شد.",
            reply_markup=admin_menu()
        )


async def matches_menu(query):
    await query.edit_message_text(
        "🎮 مسابقات",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "➕ ساخت مسابقه",
                callback_data="adm_create_match"
            )],
            [InlineKeyboardButton(
                "📋 مسابقات فعال",
                callback_data="adm_active_matches"
            )],
            [InlineKeyboardButton(
                "🔙 پنل مدیریت",
                callback_data="adm_back"
            )],
        ])
    )


async def rooms_menu(query):
    await query.edit_message_text(
        "🏠 مدیریت روم‌ها\n\n"
        "ابتدا یک مسابقه بساز.",
        reply_markup=back_admin_button()
    )


async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return False

    state = context.user_data.get("admin_state")

    if state == "waiting_match_name":

        name = update.message.text.strip()

        if not name:
            await update.message.reply_text(
                "❌ اسم مسابقه نمی‌تواند خالی باشد.\n"
                "دوباره اسم مسابقه را بفرست."
            )
            return True

        match_id = create_match(name)

        context.user_data.clear()

        await update.message.reply_text(
            "✅ مسابقه ساخته شد!\n\n"
            f"🎮 نام مسابقه:\n{name}\n\n"
            f"🆔 شناسه مسابقه: {match_id}\n\n"
            "حالا از پنل مدیریت می‌توانیم روم‌های این مسابقه را بسازیم.",
            reply_markup=admin_menu()
        )

        return True

    return False


def back_admin_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🔙 پنل مدیریت",
            callback_data="adm_back"
        )]
    ])
