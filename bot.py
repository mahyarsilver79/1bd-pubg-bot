import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
)

from database import (
    create_user,
    get_wallet,
    get_open_rooms,
    get_connection,
    register_player,
)

from admin import (
    admin_panel,
    admin_button_handler,
    new_match,
    new_room,
)


TOKEN = os.getenv("BOT_TOKEN")


def main_menu():
    keyboard = [
        [InlineKeyboardButton("🎮 ثبت‌نام مسابقه", callback_data="register")],
        [InlineKeyboardButton("📋 مسابقات من", callback_data="my_matches")],
        [InlineKeyboardButton("💰 کیف پول", callback_data="wallet")],
        [InlineKeyboardButton("📜 قوانین", callback_data="rules")],
        [InlineKeyboardButton("🎧 پشتیبانی", callback_data="support")],
    ]

    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context):
    user = update.effective_user

    create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
    )

    await update.message.reply_text(
        "🎮 به ربات 1BD PUBG خوش اومدی!\n\n"
        "مسابقه موردنظرت رو انتخاب کن:",
        reply_markup=main_menu(),
    )


async def register(update: Update, context):
    query = update.callback_query
    await query.answer()

    with get_connection() as conn:
        match = conn.execute("""
            SELECT *
            FROM matches
            WHERE status = 'open'
            ORDER BY id ASC
            LIMIT 1
        """).fetchone()

    if not match:
        await query.edit_message_text(
            "🎮 ثبت‌نام مسابقه\n\n"
            "❌ فعلاً مسابقه‌ای فعال نیست.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
            ])
        )
        return

    rooms = get_open_rooms(match["id"])

    keyboard = []

    for room in rooms:
        with get_connection() as conn:
            count = conn.execute("""
                SELECT COUNT(*) AS count
                FROM registrations
                WHERE room_id = ?
                AND status = 'active'
            """, (room["id"],)).fetchone()["count"]

        if count < room["capacity"]:
            keyboard.append([
                InlineKeyboardButton(
                    f"🎮 {room['name']} | {count}/{room['capacity']}",
                    callback_data=f"join_{room['id']}"
                )
            ])

    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت", callback_data="back")
    ])

    if len(keyboard) == 1:
        await query.edit_message_text(
            "❌ تمام روم‌ها پر شده‌اند.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await query.edit_message_text(
        f"🏆 {match['name']}\n\n"
        "روم موردنظر را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def join_room(update: Update, context):
    query = update.callback_query
    await query.answer()

    room_id = int(query.data.split("_")[1])

    success, result = register_player(
        telegram_id=query.from_user.id,
        room_id=room_id,
    )

    if not success:
        messages = {
            "user_not_found": "❌ ابتدا /start را بزن.",
            "already_registered": "⚠️ قبلاً ثبت‌نام کردی.",
            "room_not_found": "❌ روم پیدا نشد.",
            "room_full": "❌ روم پر شده است.",
        }

        await query.edit_message_text(
            messages.get(result, "❌ خطایی رخ داد."),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="register")]
            ])
        )
        return

    await query.edit_message_text(
        "✅ ثبت‌نام با موفقیت انجام شد!\n\n"
        f"👥 شماره تیم: {result}\n\n"
        "💳 پرداخت در نسخه فعلی تستی است.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back")]
        ])
    )


async def wallet(update: Update, context):
    query = update.callback_query
    await query.answer()

    balance = get_wallet(query.from_user.id)

    await query.edit_message_text(
        "💰 کیف پول\n\n"
        f"موجودی: {balance:,} تومان",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back")]
        ])
    )


async def rules(update: Update, context):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📜 قوانین مسابقات\n\n"
        "• هر تیم ۴ بازیکن دارد.\n"
        "• ظرفیت روم توسط ادمین تعیین می‌شود.\n"
        "• جایزه کیل جدا از جایزه تیمی است.\n"
        "• جوایز تیم‌های اول تا سوم جداگانه محاسبه می‌شوند.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back")]
        ])
    )


async def support(update: Update, context):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🎧 پشتیبانی\n\n"
        "برای ارتباط با پشتیبانی پیام ارسال کنید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back")]
        ])
    )


async def my_matches(update: Update, context):
    query = update.callback_query
    await query.answer()

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                rooms.name AS room_name,
                rooms.start_time,
                squads.squad_number
            FROM registrations

            JOIN users
                ON users.id = registrations.user_id

            JOIN rooms
                ON rooms.id = registrations.room_id

            LEFT JOIN squads
                ON squads.id = registrations.squad_id

            WHERE users.telegram_id = ?
            AND registrations.status = 'active'

            ORDER BY registrations.id DESC
        """, (query.from_user.id,)).fetchall()

    if not rows:
        text = "📋 مسابقات من\n\nهنوز ثبت‌نامی نداری."
    else:
        text = "📋 مسابقات من\n\n"

        for row in rows:
            text += (
                f"🎮 {row['room_name']}\n"
                f"⏰ {row['start_time'] or 'نامشخص'}\n"
                f"👥 تیم {row['squad_number']}\n\n"
            )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back")]
        ])
    )


async def back(update: Update, context):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🎮 منوی اصلی 1BD PUBG\n\n"
        "مسابقه موردنظرت رو انتخاب کن:",
        reply_markup=main_menu()
    )


async def button_handler(update: Update, context):
    query = update.callback_query

    if query.data.startswith("admin_"):
        await admin_button_handler(update, context)
        return

    if query.data == "register":
        await register(update, context)

    elif query.data.startswith("join_"):
        await join_room(update, context)

    elif query.data == "wallet":
        await wallet(update, context)

    elif query.data == "my_matches":
        await my_matches(update, context)

    elif query.data == "rules":
        await rules(update, context)

    elif query.data == "support":
        await support(update, context)

    elif query.data == "back":
        await back(update, context)


def main():

    if not TOKEN:
        raise ValueError("BOT_TOKEN تنظیم نشده است.")

    app = Application.builder().token(TOKEN).build()

    # کاربران
    app.add_handler(CommandHandler("start", start))

    # ادمین
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("newmatch", new_match))
    app.add_handler(CommandHandler("newroom", new_room))

    # دکمه‌ها
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 ربات 1BD اجرا شد...")

    app.run_polling()


if __name__ == "__main__":
    main()
