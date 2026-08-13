import os

print("🔥 ADMIN VERSION 999")


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
        [
            InlineKeyboardButton(
                "🎮 ساخت مسابقه",
                callback_data="adm_create_match"
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 ساخت روم",
                callback_data="adm_create_room"
            )
        ],
        [
            InlineKeyboardButton(
                "📋 مسابقات",
                callback_data="adm_matches"
            )
        ],
        [
            InlineKeyboardButton(
                "👥 بازیکنان",
                callback_data="adm_players"
            )
        ],
        [
            InlineKeyboardButton(
                "💰 کیف پول",
                callback_data="adm_wallets"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 آمار",
                callback_data="adm_stats"
            )
        ],
    ])


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "⛔ دسترسی غیرمجاز."
        )
        return

    context.user_data.clear()

    await update.message.reply_text(
        "👑 پنل مدیریت 1BD PUBG\n\n"
        "یک گزینه را انتخاب کن:",
        reply_markup=admin_menu()
    )


async def admin_button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if not is_admin(query.from_user.id):

        await query.edit_message_text(
            "⛔ دسترسی غیرمجاز."
        )

        return


    # =========================
    # ساخت مسابقه
    # =========================

    if query.data == "adm_create_match":

        context.user_data.clear()

        context.user_data["admin_state"] = (
            "waiting_match_name"
        )

        await query.edit_message_text(
            "🎮 ساخت مسابقه\n\n"
            "✏️ اسم مسابقه را وارد کن:\n\n"
            "مثال:\n"
            "مسابقه جمعه شب\n"
            "PUBG NIGHT\n"
            "یا فقط:\n"
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

        return


    # =========================
    # ساخت روم
    # =========================

    if query.data == "adm_create_room":

        await query.edit_message_text(
            "🏠 ساخت روم\n\n"
            "ابتدا یک مسابقه بساز.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="adm_back"
                    )
                ]
            ])
        )

        return


    # =========================
    # مسابقات
    # =========================

    if query.data == "adm_matches":

        await query.edit_message_text(
            "📋 مسابقات",
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

        return


    # =========================
    # بازیکنان
    # =========================

    if query.data == "adm_players":

        await query.edit_message_text(
            "👥 بازیکنان\n\n"
            "این بخش بعداً تکمیل می‌شود.",
            reply_markup=back_button()
        )

        return


    # =========================
    # کیف پول
    # =========================

    if query.data == "adm_wallets":

        await query.edit_message_text(
            "💰 کیف پول\n\n"
            "این بخش بعداً تکمیل می‌شود.",
            reply_markup=back_button()
        )

        return


    # =========================
    # آمار
    # =========================

    if query.data == "adm_stats":

        await query.edit_message_text(
            "📊 آمار\n\n"
            "این بخش بعداً تکمیل می‌شود.",
            reply_markup=back_button()
        )

        return


    # =========================
    # لغو
    # =========================

    if query.data == "adm_cancel":

        context.user_data.clear()

        await query.edit_message_text(
            "👑 پنل مدیریت",
            reply_markup=admin_menu()
        )

        return


    # =========================
    # برگشت
    # =========================

    if query.data == "adm_back":

        context.user_data.clear()

        await query.edit_message_text(
            "👑 پنل مدیریت 1BD PUBG",
            reply_markup=admin_menu()
        )

        return


async def handle_admin_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update.effective_user.id):
        return False


    state = context.user_data.get(
        "admin_state"
    )


    # =========================
    # اسم مسابقه
    # =========================

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
                f"🆔 ID مسابقه: {match_id}",
                reply_markup=admin_menu()
            )

        except Exception as error:

            print(
                "❌ CREATE MATCH ERROR:",
                repr(error)
            )

            await update.message.reply_text(
                "❌ خطا هنگام ساخت مسابقه.\n\n"
                "Logs را بررسی کن."
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
