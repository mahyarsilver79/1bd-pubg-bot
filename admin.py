from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import create_match, create_room, get_connection


def is_admin(user_id):
    from os import getenv

    admin_id = getenv("ADMIN_ID")

    if not admin_id:
        return False

    return str(user_id) == str(admin_id)


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_admin(user.id):
        await update.message.reply_text("⛔ دسترسی غیرمجاز.")
        return

    keyboard = [
        [InlineKeyboardButton("🎮 ساخت مسابقه", callback_data="admin_create_match")],
        [InlineKeyboardButton("🏠 مدیریت روم‌ها", callback_data="admin_rooms")],
        [InlineKeyboardButton("👥 بازیکنان", callback_data="admin_players")],
        [InlineKeyboardButton("💰 کیف پول‌ها", callback_data="admin_wallets")],
        [InlineKeyboardButton("📊 آمار", callback_data="admin_stats")],
    ]

    await update.message.reply_text(
        "👑 پنل مدیریت 1BD PUBG\n\n"
        "یکی از گزینه‌ها را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("⛔ دسترسی غیرمجاز.")
        return

    if query.data == "admin_create_match":
        await query.edit_message_text(
            "🎮 ساخت مسابقه\n\n"
            "برای ساخت مسابقه جدید از دستور زیر استفاده کن:\n\n"
            "/newmatch نام_مسابقه"
        )

    elif query.data == "admin_rooms":
        await query.edit_message_text(
            "🏠 مدیریت روم‌ها\n\n"
            "برای ساخت روم از دستور زیر استفاده کن:\n\n"
            "/newroom ID_مسابقه نام_روم ساعت ظرفیت\n\n"
            "مثال:\n"
            "/newroom 1 Room-1 22:00 64"
        )

    elif query.data == "admin_players":
        await query.edit_message_text(
            "👥 بخش بازیکنان\n\n"
            "این بخش در مرحله بعد تکمیل می‌شود."
        )

    elif query.data == "admin_wallets":
        await query.edit_message_text(
            "💰 مدیریت کیف پول\n\n"
            "این بخش در مرحله بعد تکمیل می‌شود."
        )

    elif query.data == "admin_stats":
        await query.edit_message_text(
            "📊 آمار مسابقات\n\n"
            "این بخش در مرحله بعد تکمیل می‌شود."
        )


async def new_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ دسترسی غیرمجاز.")
        return

    if not context.args:
        await update.message.reply_text(
            "فرمت صحیح:\n\n"
            "/newmatch نام_مسابقه"
        )
        return

    name = " ".join(context.args)

    match_id = create_match(name)

    await update.message.reply_text(
        "✅ مسابقه ساخته شد.\n\n"
        f"🏆 نام: {name}\n"
        f"🆔 ID مسابقه: {match_id}\n\n"
        "حالا می‌توانی برای این مسابقه روم بسازی."
    )


async def new_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ دسترسی غیرمجاز.")
        return

    if len(context.args) < 4:
        await update.message.reply_text(
            "فرمت صحیح:\n\n"
            "/newroom ID_مسابقه نام_روم ساعت ظرفیت\n\n"
            "مثال:\n"
            "/newroom 1 Room-1 22:00 64"
        )
        return

    try:
        match_id = int(context.args[0])
        name = context.args[1]
        start_time = context.args[2]
        capacity = int(context.args[3])

        room_id = create_room(
            match_id=match_id,
            name=name,
            start_time=start_time,
            capacity=capacity,
            entry_fee=50000,
            kill_prize=25000,
            first_prize=300000,
            second_prize=200000,
            third_prize=100000,
        )

        await update.message.reply_text(
            "✅ روم ساخته شد!\n\n"
            f"🏠 روم: {name}\n"
            f"⏰ ساعت: {start_time}\n"
            f"👥 ظرفیت: {capacity}\n"
            f"💰 ورودی: ۵۰٬۰۰۰ تومان\n"
            f"🔫 جایزه هر کیل: ۲۵٬۰۰۰ تومان\n"
            f"🥇 تیم اول: ۳۰۰٬۰۰۰ تومان\n"
            f"🥈 تیم دوم: ۲۰۰٬۰۰۰ تومان\n"
            f"🥉 تیم سوم: ۱۰۰٬۰۰۰ تومان\n\n"
            f"🆔 ID روم: {room_id}"
        )

    except ValueError:
        await update.message.reply_text(
            "❌ اطلاعات واردشده صحیح نیست.\n\n"
            "مثال:\n"
            "/newroom 1 Room-1 22:00 64"
        )
