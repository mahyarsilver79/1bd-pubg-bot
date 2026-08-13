import os

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
    filters
)

from database import (
    create_user,
    get_user,
    is_user_registered,
    complete_user_registration,
    get_wallet,
    get_open_rooms,
    get_room,
    create_team,
    get_captain_team,
    update_team_players,
    get_user_matches
)

from admin import (
    admin_panel,
    admin_button_handler,
    handle_admin_message
)


TOKEN = os.getenv("BOT_TOKEN")


# =========================================================
# USER MENU
# =========================================================

def main_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎮 ثبت نام روم",
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
        ]
    ])


def back_button():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔙 منوی اصلی",
                callback_data="back"
            )
        ]
    ])


# =========================================================
# START
# =========================================================

async def start(update, context):

    user = update.effective_user

    create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name
    )

    db_user = get_user(user.id)

    if not db_user or not db_user["registered"]:

        context.user_data.clear()

        context.user_data["registration_state"] = "first_name"

        await update.message.reply_text(
            "👋 خوش اومدی به 1BD PUBG\n\n"
            "برای ورود به ربات ابتدا باید ثبت‌نام کنی.\n\n"
            "فعلاً برای تست فقط مشخصات زیر رو می‌گیریم.\n\n"
            "👤 اسم خودت رو وارد کن:"
        )

        return

    await update.message.reply_text(
        "🎮 به ربات 1BD PUBG خوش اومدی!\n\n"
        "یک گزینه را انتخاب کن:",
        reply_markup=main_menu()
    )


# =========================================================
# ROOM REGISTRATION
# =========================================================

async def register(update, context):

    query = update.callback_query

    await query.answer()

    if not is_user_registered(query.from_user.id):

        await query.edit_message_text(
            "❌ ابتدا باید ثبت‌نام کاربری را کامل کنی.\n\n"
            "دوباره /start را بزن."
        )

        return

    rooms = get_open_rooms()

    if not rooms:

        await query.edit_message_text(
            "🎮 ثبت نام روم\n\n"
            "❌ فعلاً هیچ رومی فعال نیست.",
            reply_markup=back_button()
        )

        return

    keyboard = []

    for room in rooms:

        # ظرفیت = تعداد تیم
        from database import get_room_team_count

        count = get_room_team_count(room["id"])

        if count < room["capacity"]:

            keyboard.append([
                InlineKeyboardButton(
                    f"🎮 {room['name']} | "
                    f"📅 {room['room_date']} | "
                    f"⏰ {room['room_time']}",
                    callback_data=f"join_{room['id']}"
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
        "🎮 ثبت نام روم\n\n"
        "روم موردنظر را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# JOIN ROOM
# =========================================================

async def join_room(update, context):

    query = update.callback_query

    await query.answer()

    room_id = int(
        query.data.split("_")[1]
    )

    room = get_room(room_id)

    if not room:

        await query.edit_message_text(
            "❌ روم پیدا نشد.",
            reply_markup=back_button()
        )

        return

    context.user_data.clear()

    context.user_data["registration_room_id"] = room_id

    context.user_data["registration_state"] = "player1"

    await query.edit_message_text(
        f"🎮 ثبت نام در روم {room['name']}\n\n"
        "لطفاً آیدی اسمی اکانت بازی بازیکن اول را وارد کن:\n\n"
        "مثلاً همان Nickname داخل بازی."
    )


# =========================================================
# MY MATCHES
# =========================================================

async def my_matches(update, context):

    query = update.callback_query

    await query.answer()

    rows = get_user_matches(
        query.from_user.id
    )

    if not rows:

        await query.edit_message_text(
            "📋 مسابقات من\n\n"
            "هنوز در هیچ رومی ثبت‌نام نکردی.",
            reply_markup=back_button()
        )

        return

    keyboard = []

    for row in rows:

        keyboard.append([
            InlineKeyboardButton(
                f"🎮 {row['room_name']} | "
                f"📅 {row['room_date']} | "
                f"⏰ {row['room_time']}",
                callback_data=f"myroom_{row['id']}"
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
# MY ROOM DETAILS
# =========================================================

async def my_room(update, context):

    query = update.callback_query

    await query.answer()

    room_id = int(
        query.data.split("_")[1]
    )

    team = get_captain_team(
        room_id,
        query.from_user.id
    )

    room = get_room(room_id)

    if not team or not room:

        await query.edit_message_text(
            "❌ اطلاعات روم پیدا نشد.",
            reply_markup=back_button()
        )

        return

    await query.edit_message_text(
        f"🎮 {room['name']}\n\n"
        f"📅 {room['room_date']}\n"
        f"⏰ {room['room_time']}\n\n"
        "👥 بازیکنان تیم:\n\n"
        f"1️⃣ {team['player1']}\n"
        f"2️⃣ {team['player2']}\n"
        f"3️⃣ {team['player3']}\n"
        f"4️⃣ {team['player4']}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✏️ ویرایش اسامی بازیکنان",
                    callback_data=f"editplayers_{team['id']}"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ انصراف از روم",
                    callback_data=f"cancelroom_{room_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 مسابقات من",
                    callback_data="my_matches"
                )
            ]
        ])
    )


# =========================================================
# EDIT PLAYERS
# =========================================================

async def edit_players(update, context):

    query = update.callback_query

    await query.answer()

    team_id = int(
        query.data.split("_")[1]
    )

    context.user_data.clear()

    context.user_data["edit_team_id"] = team_id
    context.user_data["player_edit_state"] = "choose"

    team = None

    # پیدا کردن تیم از مسابقات کاربر
    rows = get_user_matches(
        query.from_user.id
    )

    for row in rows:

        if row["team_id"] == team_id:
            team = row
            break

    if not team:

        await query.edit_message_text(
            "❌ تیم پیدا نشد.",
            reply_markup=back_button()
        )

        return

    await query.edit_message_text(
        "✏️ کدام بازیکن را می‌خواهی ویرایش کنی؟",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f"1️⃣ {team['player1']}",
                    callback_data="editplayer_1"
                )
            ],
            [
                InlineKeyboardButton(
                    f"2️⃣ {team['player2']}",
                    callback_data="editplayer_2"
                )
            ],
            [
                InlineKeyboardButton(
                    f"3️⃣ {team['player3']}",
                    callback_data="editplayer_3"
                )
            ],
            [
                InlineKeyboardButton(
                    f"4️⃣ {team['player4']}",
                    callback_data="editplayer_4"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 برگشت",
                    callback_data=f"myroom_{team['id']}"
                )
            ]
        ])
    )


# =========================================================
# WALLET
# =========================================================

async def wallet(update, context):

    query = update.callback_query

    await query.answer()

    balance = get_wallet(
        query.from_user.id
    )

    await query.edit_message_text(
        "💰 کیف پول\n\n"
        f"💵 موجودی: {balance:,} تومان\n\n"
        "درگاه پرداخت در مرحله بعد اضافه می‌شود.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "➕ افزایش موجودی",
                    callback_data="wallet_add"
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
                    callback_data="bank_account"
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

async def rules(update, context):

    query = update.callback_query

    await query.answer()

    await query.edit_message_text(
        "📜 قوانین مسابقات\n\n"
        "قوانین بعداً تکمیل می‌شود.",
        reply_markup=back_button()
    )


# =========================================================
# SUPPORT
# =========================================================

async def support(update, context):

    query = update.callback_query

    await query.answer()

    await query.edit_message_text(
        "🎧 پشتیبانی\n\n"
        "بخش پشتیبانی بعداً تکمیل می‌شود.",
        reply_markup=back_button()
    )


# =========================================================
# BACK
# =========================================================

async def back(update, context):

    query = update.callback_query

    await query.answer()

    context.user_data.clear()

    await query.edit_message_text(
        "🎮 منوی اصلی 1BD PUBG\n\n"
        "یک گزینه را انتخاب کن:",
        reply_markup=main_menu()
    )


# =========================================================
# BUTTON HANDLER
# =========================================================

async def button_handler(update, context):

    query = update.callback_query

    data = query.data

    if data.startswith("adm_"):

        await admin_button_handler(
            update,
            context
        )

        return

    if data == "register":

        await register(update, context)

        return

    if data.startswith("join_"):

        await join_room(update, context)

        return

    if data == "my_matches":

        await my_matches(update, context)

        return

    if data.startswith("myroom_"):

        await my_room(update, context)

        return

    if data.startswith("editplayers_"):

        await edit_players(update, context)

        return

    if data.startswith("editplayer_"):

        player_number = int(
            data.split("_")[1]
        )

        context.user_data["player_edit_number"] = player_number
        context.user_data["player_edit_state"] = "waiting_name"

        await query.answer()

        await query.edit_message_text(
            f"✏️ آیدی اسمی بازیکن {player_number} را وارد کن:"
        )

        return

    if data == "wallet":

        await wallet(update, context)

        return

    if data == "rules":

        await rules(update, context)

        return

    if data == "support":

        await support(update, context)

        return

    if data == "back":

        await back(update, context)

        return


# =========================================================
# TEXT HANDLER
# =========================================================

async def text_handler(update, context):

    # اول پنل ادمین
    handled = await handle_admin_message(
        update,
        context
    )

    if handled:
        return

    state = context.user_data.get(
        "registration_state"
    )


    # =====================================================
    # USER REGISTRATION
    # =====================================================

    if state == "first_name":

        context.user_data["first_name"] = update.message.text.strip()

        context.user_data["registration_state"] = "last_name"

        await update.message.reply_text(
            "👤 فامیلت رو وارد کن:"
        )

        return


    if state == "last_name":

        context.user_data["last_name"] = update.message.text.strip()

        context.user_data["registration_state"] = "phone"

        await update.message.reply_text(
            "📱 شماره تماست رو وارد کن:"
        )

        return


    if state == "phone":

        phone = update.message.text.strip()

        user = update.effective_user

        complete_user_registration(
            telegram_id=user.id,
            first_name=context.user_data["first_name"],
            last_name=context.user_data["last_name"],
            phone=phone
        )

        context.user_data.clear()

        await update.message.reply_text(
            "✅ ثبت‌نامت با موفقیت انجام شد.\n\n"
            "حالا می‌تونی وارد پنل کاربری بشی.",
            reply_markup=main_menu()
        )

        return


    # =====================================================
    # ROOM PLAYER NAMES
    # =====================================================

    state = context.user_data.get(
        "registration_state"
    )

    if state in [
        "player1",
        "player2",
        "player3",
        "player4"
    ]:

        name = update.message.text.strip()

        if not name:

            await update.message.reply_text(
                "❌ اسم بازیکن نمی‌تواند خالی باشد."
            )

            return

        number = int(
            state[-1]
        )

        context.user_data[
            f"player{number}"
        ] = name

        if number < 4:

            next_number = number + 1

            context.user_data["registration_state"] = (
                f"player{next_number}"
            )

            await update.message.reply_text(
                f"👤 آیدی اسمی بازیکن {next_number} را وارد کن:"
            )

            return

        # چهار بازیکن کامل شد
        room_id = context.user_data[
            "registration_room_id"
        ]

        success, result = create_team(
            room_id=room_id,
            captain_telegram_id=update.effective_user.id,
            player1=context.user_data["player1"],
            player2=context.user_data["player2"],
            player3=context.user_data["player3"],
            player4=context.user_data["player4"]
        )

        if not success:

            messages = {
                "user_not_found":
                    "❌ کاربر پیدا نشد.",
                "room_not_found":
                    "❌ روم پیدا نشد.",
                "room_closed":
                    "❌ این روم بسته شده است.",
                "room_full":
                    "❌ ظرفیت روم تکمیل شده است.",
                "already_registered":
                    "⚠️ قبلاً در این روم ثبت‌نام کرده‌ای."
            }

            context.user_data.clear()

            await update.message.reply_text(
                messages.get(
                    result,
                    "❌ ثبت‌نام انجام نشد."
                ),
                reply_markup=main_menu()
            )

            return

        room = get_room(room_id)

        context.user_data.clear()

        await update.message.reply_text(
            "✅ تیم با موفقیت ثبت شد!\n\n"
            f"🎮 روم: {room['name']}\n"
            f"📅 تاریخ: {room['room_date']}\n"
            f"⏰ ساعت: {room['room_time']}\n\n"
            "👥 بازیکنان ثبت‌شده:\n"
            f"1️⃣ {context.user_data.get('player1', '')}\n"
            f"2️⃣ {context.user_data.get('player2', '')}\n"
            f"3️⃣ {context.user_data.get('player3', '')}\n"
            f"4️⃣ {context.user_data.get('player4', '')}\n\n"
            "💳 پرداخت در مرحله بعد به این بخش اضافه می‌شود.",
            reply_markup=main_menu()
        )

        return


    # =====================================================
    # EDIT PLAYER
    # =====================================================

    if context.user_data.get("player_edit_state") == "waiting_name":

        team_id = context.user_data["edit_team_id"]

        player_number = context.user_data[
            "player_edit_number"
        ]

        new_name = update.message.text.strip()

        rows = get_user_matches(
            update.effective_user.id
        )

        team_exists = False

        for row in rows:

            if row["team_id"] == team_id:
                team_exists = True
                break

        if not team_exists:

            context.user_data.clear()

            await update.message.reply_text(
                "❌ این تیم متعلق به شما نیست.",
                reply_markup=main_menu()
            )

            return

        # اطلاعات فعلی
        current = row

        players = [
            current["player1"],
            current["player2"],
            current["player3"],
            current["player4"]
        ]

        players[player_number - 1] = new_name

        update_team_players(
            team_id,
            players[0],
            players[1],
            players[2],
            players[3]
        )

        context.user_data.clear()

        await update.message.reply_text(
            "✅ اسم بازیکن با موفقیت تغییر کرد.",
            reply_markup=main_menu()
        )

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
