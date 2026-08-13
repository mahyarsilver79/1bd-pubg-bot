import os
import re
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from database import (
    create_user,
    get_wallet,
    get_open_rooms,
    get_room,
    register_team,
    get_user_rooms,
    get_team,
    update_team_player,
    cancel_team,
    get_bank_account,
    set_bank_account,
    create_withdrawal,
)

from admin import (
    admin_panel,
    admin_button_handler,
    handle_admin_message,
)


TOKEN = os.getenv("BOT_TOKEN")


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "📝 ثبت‌نام روم",
            callback_data="register"
        )],
        [InlineKeyboardButton(
            "🏆 مسابقات من",
            callback_data="my_matches"
        )],
        [InlineKeyboardButton(
            "💰 کیف پول",
            callback_data="wallet"
        )],
        [InlineKeyboardButton(
            "📜 قوانین",
            callback_data="rules"
        )],
        [InlineKeyboardButton(
            "🎧 پشتیبانی",
            callback_data="support"
        )],
    ])


def back_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🔙 منوی اصلی",
            callback_data="back"
        )]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
    )

    context.user_data.clear()

    await update.message.reply_text(
        "🎮 به ربات 1BD PUBG خوش اومدی!\n\n"
        "گزینه موردنظرت رو انتخاب کن:",
        reply_markup=main_menu()
    )


# =========================================================
# REGISTER ROOM
# =========================================================

async def register(update, context):
    query = update.callback_query
    await query.answer()

    rooms = get_open_rooms()

    if not rooms:
        await query.edit_message_text(
            "📝 ثبت‌نام روم\n\n"
            "❌ فعلاً هیچ روم فعالی وجود ندارد.",
            reply_markup=back_main()
        )
        return

    keyboard = []

    for room in rooms:
        count = get_room(room["id"])

        # تعداد واقعی تیم‌ها از دیتابیس
        from database import get_room_team_count
        team_count = get_room_team_count(room["id"])

        if team_count < room["capacity"]:
            keyboard.append([
                InlineKeyboardButton(
                    f"🏠 {room['name']} | "
                    f"📅 {room['room_date']} | "
                    f"⏰ {room['room_time']}",
                    callback_data=f"room_{room['id']}"
                )
            ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 منوی اصلی",
            callback_data="back"
        )
    ])

    if len(keyboard) == 1:
        await query.edit_message_text(
            "❌ تمام روم‌ها پر شده‌اند.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await query.edit_message_text(
        "📝 ثبت‌نام روم\n\n"
        "روم موردنظرت رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def room_details(update, context):
    query = update.callback_query
    await query.answer()

    room_id = int(query.data.split("_")[1])
    room = get_room(room_id)

    if not room:
        await query.edit_message_text(
            "❌ روم پیدا نشد.",
            reply_markup=back_main()
        )
        return

    from database import get_room_team_count
    count = get_room_team_count(room_id)

    text = (
        f"🏠 {room['name']}\n\n"
        f"📅 {room['room_date']}\n"
        f"⏰ {room['room_time']}\n"
        f"👥 ظرفیت: {room['capacity']}\n"
        f"👤 تیم‌های ثبت‌شده: {count}\n\n"
        f"💰 ورودی: {room['entry_fee']:,} تومان\n"
        f"🔫 جایزه هر کیل: {room['kill_prize']:,} تومان\n"
        f"🥇 تیم اول: {room['first_prize']:,} تومان\n"
        f"🥈 تیم دوم: {room['second_prize']:,} تومان\n"
        f"🥉 تیم سوم: {room['third_prize']:,} تومان"
    )

    keyboard = [
        [InlineKeyboardButton(
            "✅ ثبت‌نام تیم",
            callback_data=f"team_start_{room_id}"
        )],
        [InlineKeyboardButton(
            "🔙 لیست روم‌ها",
            callback_data="register"
        )],
        [InlineKeyboardButton(
            "🏠 منوی اصلی",
            callback_data="back"
        )]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# TEAM REGISTRATION INPUT
# =========================================================

async def team_start(update, context):
    query = update.callback_query
    await query.answer()

    room_id = int(query.data.split("_")[2])
    room = get_room(room_id)

    if not room:
        await query.edit_message_text(
            "❌ روم پیدا نشد.",
            reply_markup=back_main()
        )
        return

    context.user_data.clear()

    context.user_data["team_room_id"] = room_id
    context.user_data["team_state"] = "player1"

    await query.edit_message_text(
        "🎮 ثبت‌نام تیم\n\n"
        "👥 آیدی اکانت بازی بازیکن ۱ را وارد کن:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "❌ لغو",
                callback_data=f"room_{room_id}"
            )]
        ])
    )


async def handle_team_text(update, context):
    state = context.user_data.get("team_state")

    if not state:
        return False

    value = update.message.text.strip()

    if not value:
        await update.message.reply_text(
            "❌ آیدی نمی‌تواند خالی باشد."
        )
        return True

    room_id = context.user_data["team_room_id"]

    if state == "player1":
        context.user_data["player1"] = value
        context.user_data["team_state"] = "player2"

        await update.message.reply_text(
            "👥 آیدی اکانت بازی بازیکن ۲ را وارد کن:"
        )
        return True

    if state == "player2":
        context.user_data["player2"] = value
        context.user_data["team_state"] = "player3"

        await update.message.reply_text(
            "👥 آیدی اکانت بازی بازیکن ۳ را وارد کن:"
        )
        return True

    if state == "player3":
        context.user_data["player3"] = value
        context.user_data["team_state"] = "player4"

        await update.message.reply_text(
            "👥 آیدی اکانت بازی بازیکن ۴ را وارد کن:"
        )
        return True

    if state == "player4":
        context.user_data["player4"] = value
        context.user_data["team_state"] = "confirm"

        room = get_room(room_id)

        await update.message.reply_text(
            f"🏠 روم: {room['name']}\n"
            f"📅 {room['room_date']}\n"
            f"⏰ {room['room_time']}\n\n"
            "👥 بازیکنان:\n"
            f"1️⃣ {context.user_data['player1']}\n"
            f"2️⃣ {context.user_data['player2']}\n"
            f"3️⃣ {context.user_data['player3']}\n"
            f"4️⃣ {context.user_data['player4']}\n\n"
            f"💰 ورودی: {room['entry_fee']:,} تومان",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "✏️ ویرایش بازیکنان",
                    callback_data="team_edit"
                )],
                [InlineKeyboardButton(
                    "💳 پرداخت و ثبت‌نام",
                    callback_data="team_pay"
                )],
                [InlineKeyboardButton(
                    "❌ لغو",
                    callback_data=f"room_{room_id}"
                )]
            ])
        )

        return True

    return False


async def team_edit(update, context):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "✏️ کدام بازیکن را می‌خواهی ویرایش کنی؟",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"1️⃣ {context.user_data['player1']}",
                callback_data="edit_player_1"
            )],
            [InlineKeyboardButton(
                f"2️⃣ {context.user_data['player2']}",
                callback_data="edit_player_2"
            )],
            [InlineKeyboardButton(
                f"3️⃣ {context.user_data['player3']}",
                callback_data="edit_player_3"
            )],
            [InlineKeyboardButton(
                f"4️⃣ {context.user_data['player4']}",
                callback_data="edit_player_4"
            )],
            [InlineKeyboardButton(
                "🔙 ادامه ثبت‌نام",
                callback_data="team_review"
            )]
        ])
    )


async def edit_player(update, context):
    query = update.callback_query
    await query.answer()

    number = int(query.data.split("_")[2])

    context.user_data["edit_player_number"] = number
    context.user_data["team_state"] = "edit_player"

    await query.edit_message_text(
        f"👥 آیدی جدید بازیکن {number} را وارد کن:"
    )


async def team_review(update, context):
    query = update.callback_query
    await query.answer()

    room_id = context.user_data["team_room_id"]
    room = get_room(room_id)

    await query.edit_message_text(
        f"🏠 روم: {room['name']}\n\n"
        "👥 بازیکنان:\n"
        f"1️⃣ {context.user_data['player1']}\n"
        f"2️⃣ {context.user_data['player2']}\n"
        f"3️⃣ {context.user_data['player3']}\n"
        f"4️⃣ {context.user_data['player4']}\n\n"
        f"💰 ورودی: {room['entry_fee']:,} تومان",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "💳 پرداخت و ثبت‌نام",
                callback_data="team_pay"
            )],
            [InlineKeyboardButton(
                "✏️ ویرایش",
                callback_data="team_edit"
            )]
        ])
    )


async def team_pay(update, context):
    query = update.callback_query
    await query.answer()

    room_id = context.user_data.get("team_room_id")

    if not room_id:
        await query.edit_message_text(
            "❌ اطلاعات ثبت‌نام پیدا نشد.",
            reply_markup=back_main()
        )
        return

    success, result = register_team(
        telegram_id=query.from_user.id,
        room_id=room_id,
        player1=context.user_data["player1"],
        player2=context.user_data["player2"],
        player3=context.user_data["player3"],
        player4=context.user_data["player4"]
    )

    messages = {
        "room_full": "❌ ظرفیت این روم تکمیل شده است.",
        "room_closed": "❌ ثبت‌نام این روم بسته شده است.",
        "already_registered": "⚠️ قبلاً در این روم تیم ثبت کرده‌ای.",
        "insufficient_wallet": "❌ موجودی کیف پول برای پرداخت ورودی کافی نیست.",
        "room_not_found": "❌ روم پیدا نشد.",
        "user_not_found": "❌ ابتدا /start را بزن."
    }

    if not success:
        await query.edit_message_text(
            messages.get(result, "❌ ثبت‌نام انجام نشد."),
            reply_markup=back_main()
        )
        context.user_data.clear()
        return

    context.user_data.clear()

    await query.edit_message_text(
        "✅ ثبت‌نام با موفقیت انجام شد.\n\n"
        "💰 مبلغ ورودی از کیف پول کسر شد.\n"
        f"🏆 شماره تیم: {result}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🏆 مسابقات من",
                callback_data="my_matches"
            )],
            [InlineKeyboardButton(
                "🏠 منوی اصلی",
                callback_data="back"
            )]
        ])
    )


# =========================================================
# MY MATCHES
# =========================================================

async def my_matches(update, context):
    query = update.callback_query
    await query.answer()

    rows = get_user_rooms(query.from_user.id)

    if not rows:
        await query.edit_message_text(
            "🏆 مسابقات من\n\n"
            "هنوز در هیچ رومی ثبت‌نام نکردی.",
            reply_markup=back_main()
        )
        return

    keyboard = []

    for row in rows:
        keyboard.append([
            InlineKeyboardButton(
                f"🏠 {row['name']} | "
                f"📅 {row['room_date']} | "
                f"⏰ {row['room_time']}",
                callback_data=f"myroom_{row['team_id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 منوی اصلی",
            callback_data="back"
        )
    ])

    await query.edit_message_text(
        "🏆 مسابقات من\n\n"
        "روم موردنظرت را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def my_room(update, context):
    query = update.callback_query
    await query.answer()

    team_id = int(query.data.split("_")[1])
    team = get_team(team_id)

    if not team or team["captain_telegram_id"] != query.from_user.id:
        await query.edit_message_text(
            "❌ این تیم برای حساب شما نیست.",
            reply_markup=back_main()
        )
        return

    await query.edit_message_text(
        f"🏠 {team['room_name']}\n"
        f"📅 {team['room_date']}\n"
        f"⏰ {team['room_time']}\n\n"
        "🎮 بازیکنان:\n"
        f"1️⃣ {team['player1']}\n"
        f"2️⃣ {team['player2']}\n"
        f"3️⃣ {team['player3']}\n"
        f"4️⃣ {team['player4']}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "✏️ ویرایش اسامی بازیکنان",
                callback_data=f"myedit_{team_id}"
            )],
            [InlineKeyboardButton(
                "❌ انصراف از روم",
                callback_data=f"mycancel_{team_id}"
            )],
            [InlineKeyboardButton(
                "🔙 مسابقات من",
                callback_data="my_matches"
            )]
        ])
    )


async def my_edit(update, context):
    query = update.callback_query
    await query.answer()

    team_id = int(query.data.split("_")[1])
    team = get_team(team_id)

    if not team or team["captain_telegram_id"] != query.from_user.id:
        await query.edit_message_text(
            "❌ دسترسی ندارید.",
            reply_markup=back_main()
        )
        return

    await query.edit_message_text(
        "✏️ بازیکنی که می‌خواهی تغییر بدهی را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"1️⃣ {team['player1']}",
                callback_data=f"myeditplayer_{team_id}_1"
            )],
            [InlineKeyboardButton(
                f"2️⃣ {team['player2']}",
                callback_data=f"myeditplayer_{team_id}_2"
            )],
            [InlineKeyboardButton(
                f"3️⃣ {team['player3']}",
                callback_data=f"myeditplayer_{team_id}_3"
            )],
            [InlineKeyboardButton(
                f"4️⃣ {team['player4']}",
                callback_data=f"myeditplayer_{team_id}_4"
            )],
            [InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data=f"myroom_{team_id}"
            )]
        ])
    )


async def my_edit_player(update, context):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")

    team_id = int(parts[1])
    number = int(parts[2])

    team = get_team(team_id)

    if not team or team["captain_telegram_id"] != query.from_user.id:
        await query.edit_message_text(
            "❌ دسترسی ندارید.",
            reply_markup=back_main()
        )
        return

    context.user_data.clear()
    context.user_data["edit_team_id"] = team_id
    context.user_data["edit_player_number"] = number
    context.user_data["team_state"] = "my_edit_player"

    await query.edit_message_text(
        f"🎮 آیدی جدید بازیکن {number} را وارد کن:"
    )


async def my_cancel(update, context):
    query = update.callback_query
    await query.answer()

    team_id = int(query.data.split("_")[1])
    team = get_team(team_id)

    if not team or team["captain_telegram_id"] != query.from_user.id:
        await query.edit_message_text(
            "❌ دسترسی ندارید.",
            reply_markup=back_main()
        )
        return

    if not can_cancel_room(
        team["room_date"],
        team["room_time"]
    ):
        await query.edit_message_text(
            "❌ امکان انصراف وجود ندارد.\n\n"
            "انصراف فقط تا ۲ ساعت قبل از شروع روم مجاز است.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data=f"myroom_{team_id}"
                )]
            ])
        )
        return

    await query.edit_message_text(
        "⚠️ آیا از انصراف از این روم مطمئنی؟\n\n"
        "مبلغ ورودی به کیف پولت برگردانده می‌شود.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "✅ بله، انصراف",
                callback_data=f"mycancelconfirm_{team_id}"
            )],
            [InlineKeyboardButton(
                "❌ لغو",
                callback_data=f"myroom_{team_id}"
            )]
        ])
    )


def parse_room_datetime(room_date, room_time):
    """
    فرمت:
    شنبه ۲۵/۰۵
    ساعت:
    23:00

    سال جاری شمسی فرض می‌شود.
    برای جلوگیری از وابستگی به پکیج اضافی،
    تاریخ شمسی به صورت تقریبی برای کنترل ۲ ساعت استفاده می‌شود.
    """

    numbers = re.findall(r"\d+", room_date)

    if len(numbers) < 2:
        return None

    day = int(numbers[-2])
    month = int(numbers[-1])

    time_match = re.search(r"(\d{1,2}):(\d{2})", room_time)

    if not time_match:
        return None

    hour = int(time_match.group(1))
    minute = int(time_match.group(2))

    # تبدیل تقریبی جلالی به میلادی برای کنترل زمانی
    # سال جاری میلادی + ماه شمسی
    now = datetime.now()

    if month <= 6:
        month_offset = month + 2
    else:
        month_offset = month + 2

    year = now.year

    try:
        return datetime(
            year,
            max(1, min(12, month_offset - 1)),
            min(day, 28),
            hour,
            minute
        )
    except ValueError:
        return None


def can_cancel_room(room_date, room_time):
    room_dt = parse_room_datetime(room_date, room_time)

    if not room_dt:
        return True

    return datetime.now() <= room_dt - timedelta(hours=2)


async def my_cancel_confirm(update, context):
    query = update.callback_query
    await query.answer()

    team_id = int(query.data.split("_")[1])
    team = get_team(team_id)

    if not team or team["captain_telegram_id"] != query.from_user.id:
        await query.edit_message_text(
            "❌ دسترسی ندارید.",
            reply_markup=back_main()
        )
        return

    if not can_cancel_room(
        team["room_date"],
        team["room_time"]
    ):
        await query.edit_message_text(
            "❌ زمان انصراف گذشته است.",
            reply_markup=back_main()
        )
        return

    success, result = cancel_team(
        team_id,
        query.from_user.id
    )

    if not success:
        await query.edit_message_text(
            "❌ انصراف انجام نشد.",
            reply_markup=back_main()
        )
        return

    await query.edit_message_text(
        "✅ با موفقیت از روم انصراف دادی.\n\n"
        f"💰 مبلغ {result:,} تومان به کیف پولت برگشت داده شد.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🏆 مسابقات من",
                callback_data="my_matches"
            )],
            [InlineKeyboardButton(
                "🏠 منوی اصلی",
                callback_data="back"
            )]
        ])
    )


# =========================================================
# WALLET
# =========================================================

async def wallet(update, context):
    query = update.callback_query
    await query.answer()

    balance = get_wallet(query.from_user.id)
    bank = get_bank_account(query.from_user.id)

    bank_text = bank if bank else "ثبت نشده"

    await query.edit_message_text(
        "💰 کیف پول\n\n"
        f"موجودی: {balance:,} تومان\n\n"
        f"🏦 حساب بانکی:\n{bank_text}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "➕ افزایش موجودی",
                callback_data="wallet_add"
            )],
            [InlineKeyboardButton(
                "💸 برداشت",
                callback_data="wallet_withdraw"
            )],
            [InlineKeyboardButton(
                "🏦 تغییر حساب بانکی",
                callback_data="wallet_bank"
            )],
            [InlineKeyboardButton(
                "🔙 منوی اصلی",
                callback_data="back"
            )]
        ])
    )


async def wallet_add(update, context):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "➕ افزایش موجودی\n\n"
        "درگاه پرداخت در مرحله بعدی به این قسمت متصل می‌شود.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🔙 کیف پول",
                callback_data="wallet"
            )]
        ])
    )


async def wallet_bank(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["wallet_state"] = "bank"

    await query.edit_message_text(
        "🏦 شماره حساب / شبا جدید را وارد کن:"
    )


async def wallet_withdraw(update, context):
    query = update.callback_query
    await query.answer()

    bank = get_bank_account(query.from_user.id)

    if not bank:
        await query.edit_message_text(
            "❌ ابتدا باید حساب بانکی خودت را ثبت کنی.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "🏦 ثبت حساب بانکی",
                    callback_data="wallet_bank"
                )],
                [InlineKeyboardButton(
                    "🔙 کیف پول",
                    callback_data="wallet"
                )]
            ])
        )
        return

    context.user_data["wallet_state"] = "withdraw"

    await query.edit_message_text(
        "💸 برداشت\n\n"
        "مبلغ موردنظر برای برداشت را به تومان وارد کن:"
    )


# =========================================================
# GENERAL TEXT
# =========================================================

async def handle_user_text(update, context):
    wallet_state = context.user_data.get("wallet_state")

    if wallet_state == "bank":
        value = update.message.text.strip()

        if len(value) < 5:
            await update.message.reply_text(
                "❌ شماره حساب معتبر نیست."
            )
            return True

        set_bank_account(
            update.effective_user.id,
            value
        )

        context.user_data.pop("wallet_state", None)

        await update.message.reply_text(
            "✅ حساب بانکی با موفقیت ذخیره شد.",
            reply_markup=main_menu()
        )
        return True

    if wallet_state == "withdraw":
        try:
            amount = int(
                update.message.text.replace(",", "").replace("٬", "")
            )

            if amount <= 0:
                raise ValueError

        except ValueError:
            await update.message.reply_text(
                "❌ مبلغ را به صورت عدد وارد کن."
            )
            return True

        success, result = create_withdrawal(
            update.effective_user.id,
            amount
        )

        messages = {
            "no_bank": "❌ ابتدا حساب بانکی ثبت کن.",
            "insufficient_wallet": "❌ موجودی کافی نیست.",
            "pending_exists": "⚠️ یک درخواست برداشت در حال بررسی داری.",
            "invalid_amount": "❌ مبلغ نامعتبر است."
        }

        if not success:
            await update.message.reply_text(
                messages.get(
                    result,
                    "❌ درخواست برداشت ثبت نشد."
                )
            )
            return True

        context.user_data.pop("wallet_state", None)

        admin_id = os.getenv("ADMIN_ID")

        if admin_id:
            from telegram import Bot

            try:
                user = update.effective_user
                bank = get_bank_account(user.id)

                await context.bot.send_message(
                    chat_id=int(admin_id),
                    text=(
                        "💸 درخواست برداشت جدید\n\n"
                        f"👤 کاربر: {user.first_name or '-'}\n"
                        f"🔗 Username: @{user.username or '-'}\n"
                        f"🆔 Telegram ID: {user.id}\n\n"
                        f"💰 مبلغ: {amount:,} تومان\n"
                        f"🏦 حساب: {bank}\n\n"
                        f"🆔 درخواست: {result}"
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            "💸 مشاهده درخواست",
                            callback_data=f"adm_withdraw_{result}"
                        )]
                    ])
                )
            except Exception as error:
                print("WITHDRAW ADMIN MESSAGE ERROR:", repr(error))

        await update.message.reply_text(
            "✅ درخواست برداشت ثبت شد.\n\n"
            f"💰 مبلغ: {amount:,} تومان\n"
            "⏳ وضعیت: در انتظار بررسی",
            reply_markup=main_menu()
        )

        return True

    team_state = context.user_data.get("team_state")

    if team_state:
        if team_state == "edit_player":
            number = context.user_data["edit_player_number"]
            value = update.message.text.strip()

            context.user_data[f"player{number}"] = value
            context.user_data["team_state"] = "confirm"

            room_id = context.user_data["team_room_id"]
            room = get_room(room_id)

            await update.message.reply_text(
                "✅ بازیکن ویرایش شد.\n\n"
                f"1️⃣ {context.user_data['player1']}\n"
                f"2️⃣ {context.user_data['player2']}\n"
                f"3️⃣ {context.user_data['player3']}\n"
                f"4️⃣ {context.user_data['player4']}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "💳 پرداخت و ثبت‌نام",
                        callback_data="team_pay"
                    )],
                    [InlineKeyboardButton(
                        "✏️ ویرایش",
                        callback_data="team_edit"
                    )]
                ])
            )
            return True

        if team_state == "my_edit_player":
            team_id = context.user_data["edit_team_id"]
            number = context.user_data["edit_player_number"]
            value = update.message.text.strip()

            team = get_team(team_id)

            if not team or team["captain_telegram_id"] != update.effective_user.id:
                context.user_data.clear()
                await update.message.reply_text(
                    "❌ دسترسی ندارید.",
                    reply_markup=main_menu()
                )
                return True

            update_team_player(
                team_id,
                number,
                value
            )

            context.user_data.clear()

            await update.message.reply_text(
                "✅ آیدی بازیکن با موفقیت ویرایش شد.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "🏆 مسابقات من",
                        callback_data="my_matches"
                    )],
                    [InlineKeyboardButton(
                        "🏠 منوی اصلی",
                        callback_data="back"
                    )]
                ])
            )
            return True

        return await handle_team_text(update, context)

    return False


# =========================================================
# RULES / SUPPORT
# =========================================================

async def rules(update, context):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📜 قوانین\n\n"
        "بخش قوانین در مرحله بعد تکمیل می‌شود.",
        reply_markup=back_main()
    )


async def support(update, context):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🎧 پشتیبانی\n\n"
        "بخش پشتیبانی در مرحله بعد تکمیل می‌شود.",
        reply_markup=back_main()
    )


async def back(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data.clear()

    await query.edit_message_text(
        "🎮 منوی اصلی 1BD PUBG\n\n"
        "گزینه موردنظرت رو انتخاب کن:",
        reply_markup=main_menu()
    )


# =========================================================
# BUTTON HANDLER
# =========================================================

async def button_handler(update, context):
    query = update.callback_query
    data = query.data

    if data.startswith("adm_"):
        await admin_button_handler(update, context)
        return

    if data == "register":
        await register(update, context)

    elif data.startswith("room_"):
        await room_details(update, context)

    elif data.startswith("team_start_"):
        await team_start(update, context)

    elif data == "team_edit":
        await team_edit(update, context)

    elif data.startswith("edit_player_"):
        await edit_player(update, context)

    elif data == "team_review":
        await team_review(update, context)

    elif data == "team_pay":
        await team_pay(update, context)

    elif data == "my_matches":
        await my_matches(update, context)

    elif data.startswith("myroom_"):
        await my_room(update, context)

    elif data.startswith("myedit_"):
        await my_edit(update, context)

    elif data.startswith("myeditplayer_"):
        await my_edit_player(update, context)

    elif data.startswith("mycancel_"):
        await my_cancel(update, context)

    elif data.startswith("mycancelconfirm_"):
        await my_cancel_confirm(update, context)

    elif data == "wallet":
        await wallet(update, context)

    elif data == "wallet_add":
        await wallet_add(update, context)

    elif data == "wallet_bank":
        await wallet_bank(update, context)

    elif data == "wallet_withdraw":
        await wallet_withdraw(update, context)

    elif data == "rules":
        await rules(update, context)

    elif data == "support":
        await support(update, context)

    elif data == "back":
        await back(update, context)


# =========================================================
# TEXT HANDLER
# =========================================================

async def text_handler(update, context):

    handled = await handle_admin_message(
        update,
        context
    )

    if handled:
        return

    handled = await handle_user_text(
        update,
        context
    )

    if handled:
        return


# =========================================================
# MAIN
# =========================================================

def main():

    if not TOKEN:
        raise ValueError(
            "BOT_TOKEN تنظیم نشده است."
        )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("admin", admin_panel)
    )

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    print("🤖 ربات 1BD اجرا شد...")

    app.run_polling()


if __name__ == "__main__":
    main()
