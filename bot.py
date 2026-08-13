import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
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
    get_user,
    get_wallet,
    get_open_rooms,
    get_room,
    get_room_teams,
    get_room_team_count,
    create_team,
    get_captain_team,
    update_team_players,
    get_user_rooms,
)

from admin import (
    admin_panel,
    admin_button_handler,
    handle_admin_message,
)

TOKEN = os.getenv("BOT_TOKEN")


# =========================================================
# USER MENU
# =========================================================

def main_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎮 ثبت‌نام روم",
                callback_data="register"
            )
        ],
        [
            InlineKeyboardButton(
                "📋 مسابقات من",
                callback_data="my_matches"
            )
        ],
        [
            InlineKeyboardButton(
                "💰 کیف پول",
                callback_data="wallet"
            )
        ],
        [
            InlineKeyboardButton(
                "📜 قوانین",
                callback_data="rules"
            )
        ],
        [
            InlineKeyboardButton(
                "🎧 پشتیبانی",
                callback_data="support"
            )
        ],
    ])


# =========================================================
# REGISTRATION
# =========================================================

def registration_keyboard():

    keyboard = KeyboardButton(
        "📱 ارسال شماره تماس",
        request_contact=True
    )

    return ReplyKeyboardMarkup(
        [[keyboard]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
    )

    db_user = get_user(user.id)

    if not db_user or not db_user["last_name"] or not db_user["phone"]:

        context.user_data.clear()

        context.user_data["registration_state"] = "first_name"

        await update.message.reply_text(
            "👋 خوش اومدی!\n\n"
            "برای استفاده از ربات ابتدا باید ثبت‌نام کنی.\n\n"
            "👤 نام خودت را وارد کن:",
            reply_markup=ReplyKeyboardRemove()
        )

        return

    await update.message.reply_text(
        "🎮 به ربات 1BD PUBG خوش اومدی!\n\n"
        "یک گزینه را انتخاب کن:",
        reply_markup=main_menu()
    )


async def registration_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    state = context.user_data.get("registration_state")

    if not state:
        return False

    text = update.message.text.strip()

    if state == "first_name":

        if len(text) < 2:

            await update.message.reply_text(
                "❌ نام معتبر وارد کن."
            )

            return True

        context.user_data["reg_first_name"] = text
        context.user_data["registration_state"] = "last_name"

        await update.message.reply_text(
            "👤 نام خانوادگی را وارد کن:"
        )

        return True

    if state == "last_name":

        if len(text) < 2:

            await update.message.reply_text(
                "❌ نام خانوادگی معتبر وارد کن."
            )

            return True

        context.user_data["reg_last_name"] = text
        context.user_data["registration_state"] = "phone"

        await update.message.reply_text(
            "📱 شماره تماس خودت را ارسال کن:",
            reply_markup=registration_keyboard()
        )

        return True

    return False


async def registration_contact(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    state = context.user_data.get("registration_state")

    if state != "phone":
        return False

    contact = update.message.contact

    if contact.user_id and contact.user_id != update.effective_user.id:

        await update.message.reply_text(
            "❌ لطفاً شماره تماس خودت را ارسال کن."
        )

        return True

    from database import complete_user_registration

    first_name = context.user_data.get("reg_first_name")
    last_name = context.user_data.get("reg_last_name")

    complete_user_registration(
        telegram_id=update.effective_user.id,
        first_name=first_name,
        last_name=last_name,
        phone=contact.phone_number,
    )

    context.user_data.clear()

    await update.message.reply_text(
        "✅ ثبت‌نام با موفقیت انجام شد!\n\n"
        "حالا می‌تونی وارد پنل کاربری بشی.",
        reply_markup=ReplyKeyboardRemove()
    )

    await update.message.reply_text(
        "🎮 پنل کاربری 1BD PUBG",
        reply_markup=main_menu()
    )

    return True


# =========================================================
# REGISTER ROOM
# =========================================================

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    rooms = get_open_rooms()

    if not rooms:

        await query.edit_message_text(
            "🎮 ثبت‌نام روم\n\n"
            "❌ فعلاً هیچ رومی فعال نیست.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data="back"
                    )
                ]
            ])
        )

        return

    keyboard = []

    for room in rooms:

        count = get_room_team_count(room["id"])

        if count >= room["capacity"]:
            continue

        keyboard.append([
            InlineKeyboardButton(
                f"🏠 {room['name']} | "
                f"{room['room_date']} | "
                f"{room['room_time']}",
                callback_data=f"room_{room['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 بازگشت",
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
        "🎮 ثبت‌نام روم\n\n"
        "روم موردنظرت را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ROOM DETAILS
# =========================================================

async def room_details(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    room_id = int(query.data.split("_")[1])

    room = get_room(room_id)

    if not room:

        await query.edit_message_text(
            "❌ روم پیدا نشد.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data="register"
                    )
                ]
            ])
        )

        return

    count = get_room_team_count(room_id)

    text = (
        "🏠 مشخصات روم\n\n"
        f"🏷 نام: {room['name']}\n"
        f"📅 تاریخ: {room['room_date']}\n"
        f"⏰ ساعت: {room['room_time']}\n"
        f"👥 ظرفیت: {count}/{room['capacity']}\n"
        f"💰 ورودی: {room['entry_fee']:,} تومان\n\n"
        f"🔫 جایزه هر کیل: {room['kill_prize']:,} تومان\n"
        f"🥇 جایزه تیم اول: {room['first_prize']:,} تومان\n"
        f"🥈 جایزه تیم دوم: {room['second_prize']:,} تومان\n"
        f"🥉 جایزه تیم سوم: {room['third_prize']:,} تومان"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ ثبت‌نام در این روم",
                callback_data=f"team_register_{room_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 لیست روم‌ها",
                callback_data="register"
            )
        ]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# TEAM REGISTER
# =========================================================

async def team_register(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    room_id = int(
        query.data.split("_")[2]
    )

    room = get_room(room_id)

    if not room:

        await query.edit_message_text(
            "❌ روم پیدا نشد."
        )

        return

    existing = get_captain_team(
        room_id,
        query.from_user.id
    )

    if existing:

        await query.edit_message_text(
            "⚠️ شما قبلاً در این روم ثبت‌نام کرده‌ای.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "📋 مسابقات من",
                        callback_data="my_matches"
                    )
                ]
            ])
        )

        return

    count = get_room_team_count(room_id)

    if count >= room["capacity"]:

        await query.edit_message_text(
            "❌ ظرفیت روم تکمیل شده است."
        )

        return

    context.user_data.clear()

    context.user_data["team_room_id"] = room_id
    context.user_data["team_state"] = "player1"

    await query.edit_message_text(
        "👥 ثبت‌نام تیم\n\n"
        "آیدی داخل بازی بازیکن ۱ را وارد کن:"
    )


async def team_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    state = context.user_data.get("team_state")

    if not state:
        return False

    text = update.message.text.strip()

    if not text:
        return True

    index = int(state.replace("player", ""))

    context.user_data[f"player{index}"] = text

    if index < 4:

        next_index = index + 1

        context.user_data["team_state"] = f"player{next_index}"

        await update.message.reply_text(
            f"🎮 آیدی داخل بازی بازیکن {next_index} را وارد کن:"
        )

        return True

    room_id = context.user_data["team_room_id"]

    keyboard = [
        [
            InlineKeyboardButton(
                "✏️ بازیکن ۱",
                callback_data="edit_temp_1"
            ),
            InlineKeyboardButton(
                "✏️ بازیکن ۲",
                callback_data="edit_temp_2"
            )
        ],
        [
            InlineKeyboardButton(
                "✏️ بازیکن ۳",
                callback_data="edit_temp_3"
            ),
            InlineKeyboardButton(
                "✏️ بازیکن ۴",
                callback_data="edit_temp_4"
            )
        ],
        [
            InlineKeyboardButton(
                "✅ تأیید اطلاعات",
                callback_data="confirm_team"
            )
        ]
    ]

    await update.message.reply_text(
        "👥 اطلاعات تیم\n\n"
        f"1️⃣ {context.user_data['player1']}\n"
        f"2️⃣ {context.user_data['player2']}\n"
        f"3️⃣ {context.user_data['player3']}\n"
        f"4️⃣ {context.user_data['player4']}\n\n"
        "اگر اطلاعات درست است تأیید کن.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return True


async def confirm_team(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    room_id = context.user_data.get("team_room_id")

    if not room_id:

        await query.edit_message_text(
            "❌ اطلاعات ثبت‌نام پیدا نشد."
        )

        return

    room = get_room(room_id)

    if not room:

        await query.edit_message_text(
            "❌ روم پیدا نشد."
        )

        return

    count = get_room_team_count(room_id)

    if count >= room["capacity"]:

        context.user_data.clear()

        await query.edit_message_text(
            "❌ ظرفیت روم تکمیل شده است."
        )

        return

    create_team(
        room_id=room_id,
        captain_telegram_id=query.from_user.id,
        player1=context.user_data["player1"],
        player2=context.user_data["player2"],
        player3=context.user_data["player3"],
        player4=context.user_data["player4"],
    )

    context.user_data.clear()

    await query.edit_message_text(
        "✅ اطلاعات تیم ثبت شد.\n\n"
        "💳 مرحله پرداخت در مرحله بعدی به سیستم اضافه می‌شود.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📋 مسابقات من",
                    callback_data="my_matches"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 منوی اصلی",
                    callback_data="back"
                )
            ]
        ])
    )


# =========================================================
# MY MATCHES
# =========================================================

async def my_matches(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    rooms = get_user_rooms(query.from_user.id)

    if not rooms:

        await query.edit_message_text(
            "📋 مسابقات من\n\n"
            "هنوز در هیچ رومی ثبت‌نام نکردی.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 منوی اصلی",
                        callback_data="back"
                    )
                ]
            ])
        )

        return

    keyboard = []

    for room in rooms:

        keyboard.append([
            InlineKeyboardButton(
                f"🏠 {room['name']} | "
                f"{room['room_date']} | "
                f"{room['room_time']}",
                callback_data=f"myroom_{room['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 منوی اصلی",
            callback_data="back"
        )
    ])

    await query.edit_message_text(
        "📋 مسابقات من\n\n"
        "روم موردنظر را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# WALLET
# =========================================================

async def wallet(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    balance = get_wallet(
        query.from_user.id
    )

    await query.edit_message_text(
        "💰 کیف پول\n\n"
        f"موجودی: {balance:,} تومان",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "➕ افزایش موجودی",
                    callback_data="wallet_charge"
                )
            ],
            [
                InlineKeyboardButton(
                    "💸 برداشت",
                    callback_data="wallet_withdraw"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏦 تغییر حساب بانکی",
                    callback_data="wallet_bank"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 منوی اصلی",
                    callback_data="back"
                )
            ]
        ])
    )


# =========================================================
# RULES
# =========================================================

async def rules(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📜 قوانین مسابقات\n\n"
        "قوانین در حال تکمیل است.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 منوی اصلی",
                    callback_data="back"
                )
            ]
        ])
    )


# =========================================================
# SUPPORT
# =========================================================

async def support(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🎧 پشتیبانی\n\n"
        "پشتیبانی در حال آماده‌سازی است.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 منوی اصلی",
                    callback_data="back"
                )
            ]
        ])
    )


# =========================================================
# BACK
# =========================================================

async def back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    user = get_user(
        query.from_user.id
    )

    if not user or not user["last_name"] or not user["phone"]:

        await query.edit_message_text(
            "❌ ابتدا ثبت‌نام خود را کامل کن."
        )

        return

    await query.edit_message_text(
        "🎮 پنل کاربری 1BD PUBG",
        reply_markup=main_menu()
    )


# =========================================================
# BUTTON HANDLER
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query.data.startswith("adm_"):

        await admin_button_handler(
            update,
            context
        )

        return

    if query.data == "register":
        await register(update, context)

    elif query.data.startswith("room_"):
        await room_details(update, context)

    elif query.data.startswith("team_register_"):
        await team_register(update, context)

    elif query.data == "confirm_team":
        await confirm_team(update, context)

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


# =========================================================
# TEXT HANDLER
# =========================================================

async def text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    handled = await registration_text(
        update,
        context
    )

    if handled:
        return

    handled = await team_text(
        update,
        context
    )

    if handled:
        return

    handled = await handle_admin_message(
        update,
        context
    )

    if handled:
        return


# =========================================================
# CONTACT HANDLER
# =========================================================

async def contact_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    handled = await registration_contact(
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

    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "admin",
            admin_panel
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    app.add_handler(
        MessageHandler(
            filters.CONTACT,
            contact_handler
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    print(
        "🤖 ربات 1BD اجرا شد..."
    )

    app.run_polling()


if __name__ == "__main__":
    main()
