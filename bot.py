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
        [InlineKeyboardButton("🏠 ساخت روم", callback_data="adm_create_room")],
        [InlineKeyboardButton("📋 مسابقات", callback_data="adm_matches")],
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

    data = query.data

    # =========================
    # ساخت مسابقه
    # =========================

    if data == "adm_create_match":

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
                [
                    InlineKeyboardButton(
                        "❌ لغو",
                        callback_data="adm_cancel"
                    )
                ]
            ])
        )

    # =========================
    # ساخت روم
    # =========================

    elif data == "adm_create_room":

        await query.edit_message_text(
            "🏠 ساخت روم\n\n"
            "اول باید یک مسابقه بسازی.\n"
            "بعد از ساخت مسابقه، روم‌های آن را ایجاد می‌کنیم.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="adm_back"
                    )
                ]
            ])
        )

    # =========================
    # مسابقات
    # =========================

    elif data == "adm_matches":

        await query.edit_message_text(
            "📋 مسابقات\n\n"
            "از منوی اصلی می‌توانی مسابقه جدید بسازی.",
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

    # =========================
    # لغو
    # =========================

    elif data == "adm_cancel":

        context.user_data.clear()

        await query.edit_message_text(
            "👑 پنل مدیریت",
            reply_markup=admin_menu()
        )

    # =========================
    # بازگشت
    # =========================

    elif data == "adm_back":

        context.user_data.clear()

        await query.edit_message_text(
            "👑 پنل مدیریت 1BD PUBG\n\n"
            "یک گزینه را انتخاب کن:",
            reply_markup=admin_menu()
        )

    # =========================
    # بازیکنان
    # =========================

    elif data == "adm_players":

        await query.edit_message_text(
            "👥 بازیکنان\n\n"
            "این بخش بعداً تکمیل می‌شود.",
            reply_markup=back_button()
        )

    # =========================
    # کیف پول
    # =========================

    elif data == "adm_wallets":

        await query.edit_message_text(
            "💰 کیف پول\n\n"
            "این بخش بعداً تکمیل می‌شود.",
            reply_markup=back_button()
        )

    # =========================
    # آمار
    # =========================

    elif data == "adm_stats":

        await query.edit_message_text(
            "📊 آمار\n\n"
            "این بخش بعداً تکمیل می‌شود.",
            reply_markup=back_button()
        )


async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return False

    state = context.user_data.get("admin_state")

    # =========================
    # دریافت اسم مسابقه
    # =========================

    if state == "waiting_match_name":

        name = update.message.text.strip()

        if not name:

            await update.message.reply_text(
                "❌ اسم مسابقه نمی‌تواند خالی باشد.\n"
                "دوباره وارد کن:"
            )

            return True

        try:

            match_id = create_match(name)

            context.user_data.clear()

            await update.message.reply_text(
                "✅ مسابقه ساخته شد!\n\n"
                f"🎮 اسم: {name}\n"
                f"🆔 ID: {match_id}\n\n"
                "حالا می‌توانیم روم‌های این مسابقه را بسازیم.",
                reply_markup=admin_menu()
            )

        except Exception as e:

            print("CREATE MATCH ERROR:", repr(e))

            await update.message.reply_text(
                "❌ ساخت مسابقه انجام نشد.\n"
                "خطا در Logs ثبت شد."
            )

        return True

    return False


def back_button():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔙 پنل مدیریت",
                callback_data="adm_back"
            )
        ]
    ])
