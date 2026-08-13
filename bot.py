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
    get_connection,
    register_player,
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
        ]

    ])


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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
            "👋 خوش اومدی!\n\n"
            "برای استفاده از ربات ابتدا باید ثبت‌نام کنی.\n\n"
            "👤 اسم خودت رو وارد کن:",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "❌ لغو",
                        callback_data="cancel_registration"
                    )
                ]
            ])
        )

        return

    await update.message.reply_text(
        "🎮 به ربات 1BD PUBG خوش اومدی!\n\n"
        "مسابقه موردنظرت رو انتخاب کن:",
        reply_markup=main_menu()
    )


# =========================================================
# USER REGISTRATION
# =========================================================

async def handle_user_registration(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    state = context.user_data.get(
        "registration_state"
    )

    if not state:
        return False

    text = update.message.text.strip()

    if not text:
        return True

    if state == "first_name":

        context.user_data["reg_first_name"] = text

        context.user_data[
            "registration_state"
        ] = "last_name"

        await update.message.reply_text(
            "👤 فامیلی خودت رو وارد کن:"
        )

        return True

    if state == "last_name":

        context.user_data["reg_last_name"] = text

        context.user_data[
            "registration_state"
        ] = "phone"

        await update.message.reply_text(
            "📱 شماره تماس خودت رو وارد کن:"
        )

        return True

    if state == "phone":

        user = update.effective_user

        first_name = context.user_data.get(
            "reg_first_name",
            ""
        )

        last_name = context.user_data.get(
            "reg_last_name",
            ""
        )

        phone = text

        complete_user_registration(
            telegram_id=user.id,
            first_name=first_name,
            last_name=last_name,
            phone=phone
        )

        context.user_data.clear()

        await update.message.reply_text(
            "✅ ثبت‌نام با موفقیت انجام شد!\n\n"
            "اطلاعات اکانتت ثبت شد.\n"
            f"🆔 ID: {user.id}\n"
            f"👤 Username: @{user.username if user.username else 'ندارد'}\n\n"
            "حالا می‌تونی وارد پنل کاربری بشی.",
            reply_markup=main_menu()
        )

        return True

    return False


# =========================================================
# REGISTER ROOM
# =========================================================

async def register(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if not is_user_registered(
        query.from_user.id
    ):

        await query.edit_message_text(
            "❌ ابتدا باید ثبت‌نام کاربری خودت رو کامل کنی.\n"
            "دستور /start رو بزن.",
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

    with get_connection() as conn:

        rooms = conn.execute("""
            SELECT *
            FROM rooms
            WHERE status = 'open'
            ORDER BY id ASC
        """).fetchall()

    keyboard = []

    for room in rooms:

        result = conn_count = None

        with get_connection() as conn:

            result = conn.execute("""
                SELECT COUNT(*) AS count
                FROM registrations
                WHERE room_id = ?
            """, (
                room["id"],
            )).fetchone()

        count = result["count"]

        if count < room["capacity"]:

            keyboard.append([
                InlineKeyboardButton(
                    (
                        f"🎮 {room['name']} | "
                        f"📅 {room['room_date']} | "
                        f"⏰ {room['room_time']}"
                    ),
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
            "🎮 ثبت‌نام روم\n\n"
            "❌ فعلاً روم فعالی وجود ندارد.",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

        return

    await query.edit_message_text(
        "🎮 ثبت‌نام روم\n\n"
        "روم موردنظر خودت رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# JOIN ROOM
# =========================================================

async def join_room(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    room_id = int(
        query.data.split("_")[1]
    )

    success, result = register_player(
        telegram_id=query.from_user.id,
        room_id=room_id
    )

    if not success:

        messages = {

            "user_not_found":
                "❌ ابتدا ثبت‌نام کن.",

            "already_registered":
                "⚠️ قبلاً در این روم ثبت‌نام کردی.",

            "room_not_found":
                "❌ روم پیدا نشد.",

            "room_full":
                "❌ این روم پر شده است."

        }

        await query.edit_message_text(
            messages.get(
                result,
                "❌ خطایی رخ داد."
            ),
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

    await query.edit_message_text(
        "✅ ثبت‌نام با موفقیت انجام شد!\n\n"
        f"👥 شماره تیم: {result}\n\n"
        "💳 پرداخت در مرحله بعد اضافه می‌شود.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📋 مسابقات من",
                    callback_data="my_matches"
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
# MY MATCHES
# =========================================================

async def my_matches(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    rows = get_user_matches(
        query.from_user.id
    )

    if not rows:

        text = (
            "📋 مسابقات من\n\n"
            "هنوز در هیچ رومی ثبت‌نام نکردی."
        )

    else:

        text = "📋 مسابقات من\n\n"

        for row in rows:

            text += (
                f"🎮 {row['name']}\n"
                f"📅 {row['room_date']}\n"
                f"⏰ {row['room_time']}\n\n"
            )

    await query.edit_message_text(
        text,
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
# WALLET
# =========================================================

async def wallet(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if not is_user_registered(
        query.from_user.id
    ):
        await query.edit_message_text(
            "❌ ابتدا ثبت‌نام کن.",
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

    balance = get_wallet(
        query.from_user.id
    )

    await query.edit_message_text(
        "💰 کیف پول\n\n"
        f"💵 موجودی: {balance:,} تومان",
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
        "پشتیبانی در حال تکمیل است.",
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

    if not is_user_registered(
        query.from_user.id
    ):

        await query.edit_message_text(
            "❌ ابتدا باید ثبت‌نام کنی.\n"
            "دستور /start رو بزن."
        )

        return

    await query.edit_message_text(
        "🎮 منوی اصلی 1BD PUBG\n\n"
        "مسابقه موردنظرت رو انتخاب کن:",
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

    if query.data == "cancel_registration":

        context.user_data.clear()

        await query.answer()

        await query.edit_message_text(
            "❌ ثبت‌نام لغو شد.\n\n"
            "برای شروع دوباره /start رو بزن."
        )

        return

    if query.data == "register":

        await register(
            update,
            context
        )

    elif query.data.startswith("join_"):

        await join_room(
            update,
            context
        )

    elif query.data == "my_matches":

        await my_matches(
            update,
            context
        )

    elif query.data == "wallet":

        await wallet(
            update,
            context
        )

    elif query.data == "rules":

        await rules(
            update,
            context
        )

    elif query.data == "support":

        await support(
            update,
            context
        )

    elif query.data == "back":

        await back(
            update,
            context
        )


# =========================================================
# TEXT HANDLER
# =========================================================

async def text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    # اول ثبت‌نام کاربر
    handled = await handle_user_registration(
        update,
        context
    )

    if handled:
        return

    # بعد پیام‌های ادمین
    handled = await handle_admin_message(
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
