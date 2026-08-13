import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from database import (
    create_user,
    get_user,
    get_wallet,
    get_open_rooms,
    find_available_room,
    register_player,
    cancel_registration,
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def show_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # فعلاً اولین مسابقه فعال را پیدا می‌کنیم
    # سیستم پنل ادمین را در مرحله بعد اضافه می‌کنیم.

    from database import get_connection

    conn = get_connection()

    match = conn.execute("""
        SELECT *
        FROM matches
        WHERE status = 'open'
        ORDER BY id ASC
        LIMIT 1
    """).fetchone()

    conn.close()

    if not match:
        await query.edit_message_text(
            "🎮 ثبت‌نام مسابقه\n\n"
            "❌ فعلاً هیچ مسابقه‌ای فعال نیست.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
            ])
        )
        return

    rooms = get_open_rooms(match["id"])

    if not rooms:
        await query.edit_message_text(
            "🎮 ثبت‌نام مسابقه\n\n"
            "❌ فعلاً هیچ رومی برای ثبت‌نام فعال نیست.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
            ])
        )
        return

    keyboard = []

    for room in rooms:
        count = 0

        with get_connection() as conn:
            result = conn.execute("""
                SELECT COUNT(*) AS count
                FROM registrations
                WHERE room_id = ?
                AND status = 'active'
            """, (room["id"],)).fetchone()

            count = result["count"]

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
            "🎮 ثبت‌نام مسابقه\n\n"
            "❌ تمام روم‌ها پر شده‌اند.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await query.edit_message_text(
        f"🏆 {match['name']}\n\n"
        "روم موردنظر را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def join_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    room_id = int(query.data.split("_")[1])

    success, result = register_player(
        telegram_id=user.id,
        room_id=room_id,
    )

    if not success:

        messages = {
            "user_not_found": "❌ ابتدا /start را بزن.",
            "already_registered": "⚠️ تو قبلاً در این روم ثبت‌نام کردی.",
            "room_not_found": "❌ این روم پیدا نشد.",
            "room_full": "❌ این روم پر شده است.",
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
        "💳 مرحله پرداخت در نسخه فعلی غیرفعال است.\n"
        "درگاه پرداخت را بعداً اضافه می‌کنیم.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 مسابقات من", callback_data="my_matches")],
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back")]
        ])
    )


async def my_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT
                registrations.id,
                registrations.room_id,
                registrations.squad_id,
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
        """, (user.id,)).fetchall()

    if not rows:
        text = (
            "📋 مسابقات من\n\n"
            "هنوز در هیچ مسابقه‌ای ثبت‌نام نکردی."
        )
    else:
        text = "📋 مسابقات من\n\n"

        for row in rows:
            text += (
                f"🎮 {row['room_name']}\n"
                f"⏰ ساعت: {row['start_time'] or 'تعیین نشده'}\n"
                f"👥 تیم: {row['squad_number']}\n\n"
            )

    keyboard = [
        [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    balance = get_wallet(user.id)

    await query.edit_message_text(
        "💰 کیف پول\n\n"
        f"موجودی: {balance:,} تومان\n\n"
        "درگاه پرداخت و برداشت در مرحله بعد اضافه می‌شود.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back")]
        ])
    )


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📜 قوانین مسابقات\n\n"
        "• هر تیم شامل ۴ بازیکن است.\n"
        "• ظرفیت هر روم توسط ادمین تعیین می‌شود.\n"
        "• جایزه هر کیل طبق تنظیمات مسابقه محاسبه می‌شود.\n"
        "• جوایز تیم‌های اول تا سوم جداگانه محاسبه می‌شوند.\n"
        "• قوانین نهایی قبل از شروع مسابقه اعلام می‌شود.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back")]
        ])
    )


async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🎧 پشتیبانی\n\n"
        "برای ارتباط با پشتیبانی پیام خود را ارسال کنید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data="back")]
        ])
    )


async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🎮 منوی اصلی 1BD PUBG\n\n"
        "مسابقه موردنظرت رو انتخاب کن:",
        reply_markup=main_menu()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.data == "register":
        await show_register(update, context)

    elif query.data.startswith("join_"):
        await join_room(update, context)

    elif query.data == "my_matches":
        await my_matches(update, context)

    elif query.data == "wallet":
        await wallet(update, context)

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

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 ربات 1BD اجرا شد...")

    app.run_polling()


if __name__ == "__main__":
    main()
