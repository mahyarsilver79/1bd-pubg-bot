import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import ContextTypes

from database import (
    create_room,
    get_rooms,
    get_room,
    get_room_teams,
    get_room_team_count,
    update_room,
    delete_room_and_refund,
    get_connection,
    add_wallet
)


# =========================================================
# ADMIN
# =========================================================

def is_admin(user_id):

    admin_id = os.getenv("ADMIN_ID")

    if not admin_id:
        return False

    return str(user_id) == str(admin_id)


# =========================================================
# ADMIN MENU
# =========================================================

def admin_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🏠 ساخت روم",
                callback_data="adm_create_room"
            )
        ],
        [
            InlineKeyboardButton(
                "📋 لیست روم‌ها",
                callback_data="adm_rooms"
            )
        ],
        [
            InlineKeyboardButton(
                "💰 مدیریت کیف پول کاربران",
                callback_data="adm_wallet"
            )
        ]
    ])


def back_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔙 پنل مدیریت",
                callback_data="adm_back"
            )
        ]
    ])


def cancel_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "❌ لغو",
                callback_data="adm_cancel"
            )
        ]
    ])


# =========================================================
# ADMIN PANEL
# =========================================================

async def admin_panel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update.effective_user.id):

        await update.message.reply_text(
            "⛔ دسترسی غیرمجاز."
        )

        return

    context.user_data.clear()

    await update.message.reply_text(
        "👑 پنل مدیریت\n\n"
        "یک گزینه را انتخاب کن:",
        reply_markup=admin_menu()
    )


# =========================================================
# ADMIN BUTTON HANDLER
# =========================================================

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


    # =====================================================
    # CREATE ROOM
    # =====================================================

    if query.data == "adm_create_room":

        context.user_data.clear()

        context.user_data["admin_state"] = "room_name"

        await query.edit_message_text(
            "🏠 ساخت روم\n\n"
            "📝 اسم روم را وارد کن:",
            reply_markup=cancel_menu()
        )

        return


    # =====================================================
    # ROOM LIST
    # =====================================================

    if query.data == "adm_rooms":

        rooms = get_rooms()

        if not rooms:

            await query.edit_message_text(
                "📋 لیست روم‌ها\n\n"
                "❌ هنوز هیچ رومی ساخته نشده.",
                reply_markup=back_menu()
            )

            return


        keyboard = []

        for room in rooms:

            keyboard.append([
                InlineKeyboardButton(
                    f"🏠 {room['name']} | "
                    f"📅 {room['room_date']} | "
                    f"⏰ {room['room_time']}",
                    callback_data=f"adm_room_{room['id']}"
                )
            ])


        keyboard.append([
            InlineKeyboardButton(
                "🔙 پنل مدیریت",
                callback_data="adm_back"
            )
        ])


        await query.edit_message_text(
            "📋 لیست روم‌ها\n\n"
            "روم موردنظر را انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return


    # =====================================================
    # ROOM DETAILS
    # =====================================================

    if query.data.startswith("adm_room_"):

        room_id = int(
            query.data.split("_")[2]
        )

        room = get_room(room_id)

        if not room:

            await query.edit_message_text(
                "❌ این روم پیدا نشد.",
                reply_markup=back_menu()
            )

            return


        team_count = get_room_team_count(room_id)


        status_text = (
            "🟢 فعال"
            if room["status"] == "open"
            else "🔴 بسته"
        )


        text = (
            "🏠 مشخصات روم\n\n"

            f"🏷 نام روم: {room['name']}\n"
            f"📅 تاریخ: {room['room_date']}\n"
            f"⏰ ساعت: {room['room_time']}\n"
            f"👥 ظرفیت: {room['capacity']}\n"
            f"👤 تعداد تیم‌ها: {team_count}\n"
            f"💰 ورودی: {room['entry_fee']:,} تومان\n\n"

            f"🔫 جایزه هر کیل: "
            f"{room['kill_prize']:,} تومان\n"

            f"🥇 جایزه تیم اول: "
            f"{room['first_prize']:,} تومان\n"

            f"🥈 جایزه تیم دوم: "
            f"{room['second_prize']:,} تومان\n"

            f"🥉 جایزه تیم سوم: "
            f"{room['third_prize']:,} تومان\n\n"

            f"📌 وضعیت: {status_text}\n"
            f"🆔 شماره روم: {room['id']}"
        )


        keyboard = [

            [
                InlineKeyboardButton(
                    "👥 بازیکنان روم",
                    callback_data=f"adm_players_{room_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    "✏️ ویرایش روم",
                    callback_data=f"adm_edit_{room_id}"
                ),

                InlineKeyboardButton(
                    "🗑 حذف روم",
                    callback_data=f"adm_delete_{room_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔙 لیست روم‌ها",
                    callback_data="adm_rooms"
                )
            ],

            [
                InlineKeyboardButton(
                    "🏠 پنل مدیریت",
                    callback_data="adm_back"
                )
            ]

        ]


        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return


    # =====================================================
    # PLAYERS / TEAMS
    # =====================================================

    if query.data.startswith("adm_players_"):

        room_id = int(
            query.data.split("_")[2]
        )

        room = get_room(room_id)

        if not room:

            await query.edit_message_text(
                "❌ روم پیدا نشد.",
                reply_markup=back_menu()
            )

            return


        teams = get_room_teams(room_id)


        if not teams:

            text = (
                f"👥 بازیکنان روم\n\n"
                f"🏠 {room['name']}\n\n"
                "❌ هنوز هیچ تیمی ثبت‌نام نکرده."
            )

        else:

            text = (
                f"👥 بازیکنان روم\n\n"
                f"🏠 {room['name']}\n\n"
            )


            for index, team in enumerate(
                teams,
                start=1
            ):

                captain = (
                    team["captain_first_name"]
                    or team["captain_username"]
                    or "بدون نام"
                )

                captain_username = (
                    f"@{team['captain_username']}"
                    if team["captain_username"]
                    else "بدون username"
                )


                text += (
                    f"🏆 تیم {index} — جایگاه {index}\n"
                    f"👑 کاپیتان: {captain}\n"
                    f"📱 آیدی تلگرام: {captain_username}\n"
                    f"🆔 Telegram ID: "
                    f"{team['captain_telegram_id']}\n\n"

                    f"1️⃣ {team['player1']}\n"
                    f"2️⃣ {team['player2']}\n"
                    f"3️⃣ {team['player3']}\n"
                    f"4️⃣ {team['player4']}\n\n"
                )


        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🔙 مشخصات روم",
                        callback_data=f"adm_room_{room_id}"
                    )
                ]

            ])
        )

        return


    # =====================================================
    # DELETE CONFIRM
    # =====================================================

    if query.data.startswith("adm_delete_"):

        room_id = int(
            query.data.split("_")[2]
        )

        room = get_room(room_id)

        if not room:

            await query.edit_message_text(
                "❌ روم پیدا نشد.",
                reply_markup=back_menu()
            )

            return


        teams = get_room_team_count(room_id)


        await query.edit_message_text(

            "⚠️ حذف روم\n\n"

            f"🏠 {room['name']}\n\n"

            f"👥 تعداد تیم‌های ثبت‌نام‌شده: {teams}\n\n"

            "با حذف روم:\n"
            "💰 مبلغ ورودی تمام کاپیتان‌ها به کیف پولشان برمی‌گردد.\n"
            "📩 به کاپیتان‌ها اطلاع داده می‌شود.\n\n"

            "آیا مطمئنی؟",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "✅ بله، حذف کن",
                        callback_data=f"adm_delete_confirm_{room_id}"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "❌ انصراف",
                        callback_data=f"adm_room_{room_id}"
                    )
                ]

            ])
        )

        return


    # =====================================================
    # DELETE ACTION
    # =====================================================

    if query.data.startswith("adm_delete_confirm_"):

        room_id = int(
            query.data.split("_")[3]
        )

        room = get_room(room_id)

        if not room:

            await query.edit_message_text(
                "❌ روم پیدا نشد.",
                reply_markup=back_menu()
            )

            return


        captains = delete_room_and_refund(
            room_id
        )


        for telegram_id in captains:

            try:

                await context.bot.send_message(

                    chat_id=telegram_id,

                    text=(
                        "⚠️ اطلاعیه روم\n\n"
                        f"روم «{room['name']}» توسط مدیریت حذف شد.\n\n"
                        f"💰 مبلغ {room['entry_fee']:,} تومان "
                        "به کیف پول شما برگشت داده شد."
                    )

                )

            except Exception as error:

                print(
                    "CAPTAIN MESSAGE ERROR:",
                    repr(error)
                )


        await query.edit_message_text(

            "✅ روم با موفقیت حذف شد.\n\n"

            f"🏠 {room['name']}\n"
            f"💰 مبلغ ورودی به {len(captains)} کاپیتان برگشت داده شد.",

            reply_markup=back_menu()
        )

        return


    # =====================================================
    # EDIT ROOM
    # =====================================================

    if query.data.startswith("adm_edit_"):

        room_id = int(
            query.data.split("_")[2]
        )

        room = get_room(room_id)

        if not room:

            await query.edit_message_text(
                "❌ روم پیدا نشد.",
                reply_markup=back_menu()
            )

            return


        context.user_data.clear()

        context.user_data["edit_room_id"] = room_id

        await show_edit_menu(
            query,
            room_id
        )

        return


    # =====================================================
    # EDIT NAME
    # =====================================================

    if query.data.startswith("adm_edit_name_"):

        room_id = int(
            query.data.split("_")[3]
        )

        context.user_data.clear()

        context.user_data["edit_room_id"] = room_id
        context.user_data["admin_state"] = "edit_name"

        room = get_room(room_id)

        await query.edit_message_text(
            "✏️ تغییر نام روم\n\n"
            f"نام فعلی:\n{room['name']}\n\n"
            "نام جدید را وارد کن:",
            reply_markup=cancel_menu()
        )

        return


    # =====================================================
    # EDIT DATE
    # =====================================================

    if query.data.startswith("adm_edit_date_"):

        room_id = int(
            query.data.split("_")[3]
        )

        context.user_data.clear()

        context.user_data["edit_room_id"] = room_id
        context.user_data["admin_state"] = "edit_date"

        room = get_room(room_id)

        await query.edit_message_text(
            "📅 تغییر تاریخ روم\n\n"
            f"تاریخ فعلی:\n{room['room_date']}\n\n"
            "تاریخ جدید را وارد کن:",
            reply_markup=cancel_menu()
        )

        return


    # =====================================================
    # EDIT TIME
    # =====================================================

    if query.data.startswith("adm_edit_time_"):

        room_id = int(
            query.data.split("_")[3]
        )

        context.user_data.clear()

        context.user_data["edit_room_id"] = room_id
        context.user_data["admin_state"] = "edit_time"

        room = get_room(room_id)

        await query.edit_message_text(
            "⏰ تغییر ساعت روم\n\n"
            f"ساعت فعلی:\n{room['room_time']}\n\n"
            "ساعت جدید را وارد کن:",
            reply_markup=cancel_menu()
        )

        return


    # =====================================================
    # WALLET MENU
    # =====================================================

    if query.data == "adm_wallet":

        context.user_data.clear()

        context.user_data["admin_state"] = "wallet_search"

        await query.edit_message_text(
            "💰 مدیریت کیف پول کاربران\n\n"
            "آیدی تلگرام یا username کاربر را وارد کن.\n\n"
            "مثال:\n"
            "@username\n"
            "یا\n"
            "123456789",
            reply_markup=cancel_menu()
        )

        return


    # =====================================================
    # WALLET USER
    # =====================================================

    if query.data.startswith("adm_wallet_user_"):

        user_id = int(
            query.data.split("_")[3]
        )

        with get_connection() as conn:

            user = conn.execute("""
                SELECT *
                FROM users
                WHERE id = ?
            """, (user_id,)).fetchone()

        if not user:

            await query.edit_message_text(
                "❌ کاربر پیدا نشد.",
                reply_markup=back_menu()
            )

            return


        username = (
            f"@{user['username']}"
            if user["username"]
            else "ندارد"
        )


        text = (
            "👤 مشخصات کاربر\n\n"
            f"🆔 Telegram ID: {user['telegram_id']}\n"
            f"👤 Username: {username}\n"
            f"📛 نام: {user['first_name'] or 'ندارد'}\n\n"
            f"💰 موجودی کیف پول:\n"
            f"{user['wallet']:,} تومان"
        )


        keyboard = [

            [
                InlineKeyboardButton(
                    "➕ افزایش موجودی",
                    callback_data=f"adm_wallet_add_{user_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    "➖ کاهش موجودی",
                    callback_data=f"adm_wallet_sub_{user_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔄 بروزرسانی",
                    callback_data=f"adm_wallet_user_{user_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔙 مدیریت کیف پول",
                    callback_data="adm_wallet"
                )
            ]

        ]


        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return


    # =====================================================
    # WALLET ADD
    # =====================================================

    if query.data.startswith("adm_wallet_add_"):

        user_id = int(
            query.data.split("_")[3]
        )

        context.user_data.clear()

        context.user_data["wallet_user_id"] = user_id
        context.user_data["admin_state"] = "wallet_add"

        await query.edit_message_text(
            "➕ افزایش موجودی\n\n"
            "مبلغ را به تومان وارد کن:",
            reply_markup=cancel_menu()
        )

        return


    # =====================================================
    # WALLET SUBTRACT
    # =====================================================

    if query.data.startswith("adm_wallet_sub_"):

        user_id = int(
            query.data.split("_")[3]
        )

        context.user_data.clear()

        context.user_data["wallet_user_id"] = user_id
        context.user_data["admin_state"] = "wallet_sub"

        await query.edit_message_text(
            "➖ کاهش موجودی\n\n"
            "مبلغ را به تومان وارد کن:",
            reply_markup=cancel_menu()
        )

        return


    # =====================================================
    # BACK
    # =====================================================

    if query.data == "adm_back":

        context.user_data.clear()

        await query.edit_message_text(
            "👑 پنل مدیریت\n\n"
            "یک گزینه را انتخاب کن:",
            reply_markup=admin_menu()
        )

        return


    # =====================================================
    # CANCEL
    # =====================================================

    if query.data == "adm_cancel":

        context.user_data.clear()

        await query.edit_message_text(
            "👑 پنل مدیریت\n\n"
            "یک گزینه را انتخاب کن:",
            reply_markup=admin_menu()
        )

        return


# =========================================================
# EDIT MENU
# =========================================================

async def show_edit_menu(query, room_id):

    room = get_room(room_id)

    keyboard = [

        [
            InlineKeyboardButton(
                "🏷 تغییر نام",
                callback_data=f"adm_edit_name_{room_id}"
            )
        ],

        [
            InlineKeyboardButton(
                "📅 تغییر تاریخ",
                callback_data=f"adm_edit_date_{room_id}"
            )
        ],

        [
            InlineKeyboardButton(
                "⏰ تغییر ساعت",
                callback_data=f"adm_edit_time_{room_id}"
            )
        ],

        [
            InlineKeyboardButton(
                "🔙 مشخصات روم",
                callback_data=f"adm_room_{room_id}"
            )
        ]

    ]

    await query.edit_message_text(
        "✏️ ویرایش روم\n\n"
        f"🏠 {room['name']}\n"
        f"📅 {room['room_date']}\n"
        f"⏰ {room['room_time']}\n\n"
        "فقط موردی که می‌خواهی تغییر کند را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ADMIN TEXT HANDLER
# =========================================================

async def handle_admin_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update.effective_user.id):

        return False


    state = context.user_data.get(
        "admin_state"
    )

    text = update.message.text.strip()


    # =====================================================
    # WALLET SEARCH
    # =====================================================

    if state == "wallet_search":

        search = text.strip()

        if search.startswith("@"):

            search = search[1:]


        with get_connection() as conn:

            if search.isdigit():

                user = conn.execute("""
                    SELECT *
                    FROM users
                    WHERE telegram_id = ?
                """, (
                    int(search),
                )).fetchone()

            else:

                user = conn.execute("""
                    SELECT *
                    FROM users
                    WHERE LOWER(username) = LOWER(?)
                """, (
                    search,
                )).fetchone()


        if not user:

            await update.message.reply_text(
                "❌ کاربر پیدا نشد.\n\n"
                "آیدی تلگرام یا username را درست وارد کن.",
                reply_markup=cancel_menu()
            )

            return True


        context.user_data.clear()

        username = (
            f"@{user['username']}"
            if user["username"]
            else "ندارد"
        )


        await update.message.reply_text(

            "👤 کاربر پیدا شد.\n\n"

            f"🆔 Telegram ID: {user['telegram_id']}\n"
            f"👤 Username: {username}\n"
            f"📛 نام: {user['first_name'] or 'ندارد'}\n"
            f"💰 موجودی: {user['wallet']:,} تومان",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "➕ افزایش موجودی",
                        callback_data=f"adm_wallet_add_{user['id']}"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "➖ کاهش موجودی",
                        callback_data=f"adm_wallet_sub_{user['id']}"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "🔙 مدیریت کیف پول",
                        callback_data="adm_wallet"
                    )
                ]

            ])
        )

        return True


    # =====================================================
    # WALLET ADD
    # =====================================================

    if state == "wallet_add":

        try:

            amount = int(
                text.replace(",", "")
            )

            if amount <= 0:
                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ مبلغ باید یک عدد مثبت باشد.",
                reply_markup=cancel_menu()
            )

            return True


        user_id = context.user_data["wallet_user_id"]


        with get_connection() as conn:

            user = conn.execute("""
                SELECT *
                FROM users
                WHERE id = ?
            """, (
                user_id,
            )).fetchone()


        if not user:

            context.user_data.clear()

            await update.message.reply_text(
                "❌ کاربر پیدا نشد.",
                reply_markup=admin_menu()
            )

            return True


        success = add_wallet(
            user["telegram_id"],
            amount,
            "شارژ کیف پول توسط مدیریت"
        )


        if not success:

            await update.message.reply_text(
                "❌ خطا در افزایش موجودی."
            )

            return True


        new_balance = (
            user["wallet"] + amount
        )


        context.user_data.clear()


        await update.message.reply_text(

            "✅ موجودی با موفقیت افزایش پیدا کرد.\n\n"

            f"👤 کاربر: "
            f"{user['username'] or user['telegram_id']}\n"

            f"➕ مبلغ شارژ: "
            f"{amount:,} تومان\n"

            f"💰 موجودی جدید: "
            f"{new_balance:,} تومان",

            reply_markup=admin_menu()
        )


        try:

            await context.bot.send_message(

                chat_id=user["telegram_id"],

                text=(
                    "💰 کیف پول شما شارژ شد.\n\n"
                    f"➕ مبلغ: {amount:,} تومان\n"
                    f"💰 موجودی جدید: {new_balance:,} تومان"
                )

            )

        except Exception as error:

            print(
                "WALLET USER MESSAGE ERROR:",
                repr(error)
            )


        return True


    # =====================================================
    # WALLET SUBTRACT
    # =====================================================

    if state == "wallet_sub":

        try:

            amount = int(
                text.replace(",", "")
            )

            if amount <= 0:
                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ مبلغ باید یک عدد مثبت باشد.",
                reply_markup=cancel_menu()
            )

            return True


        user_id = context.user_data["wallet_user_id"]


        with get_connection() as conn:

            user = conn.execute("""
                SELECT *
                FROM users
                WHERE id = ?
            """, (
                user_id,
            )).fetchone()


        if not user:

            context.user_data.clear()

            await update.message.reply_text(
                "❌ کاربر پیدا نشد.",
                reply_markup=admin_menu()
            )

            return True


        if user["wallet"] < amount:

            await update.message.reply_text(
                "❌ موجودی کاربر کافی نیست.\n\n"
                f"💰 موجودی فعلی: "
                f"{user['wallet']:,} تومان",
                reply_markup=cancel_menu()
            )

            return True


        success = add_wallet(
            user["telegram_id"],
            -amount,
            "کاهش موجودی توسط مدیریت"
        )


        if not success:

            await update.message.reply_text(
                "❌ خطا در کاهش موجودی."
            )

            return True


        new_balance = (
            user["wallet"] - amount
        )


        context.user_data.clear()


        await update.message.reply_text(

            "✅ موجودی با موفقیت کاهش پیدا کرد.\n\n"

            f"👤 کاربر: "
            f"{user['username'] or user['telegram_id']}\n"

            f"➖ مبلغ کسر شده: "
            f"{amount:,} تومان\n"

            f"💰 موجودی جدید: "
            f"{new_balance:,} تومان",

            reply_markup=admin_menu()
        )


        try:

            await context.bot.send_message(

                chat_id=user["telegram_id"],

                text=(
                    "💰 موجودی کیف پول شما تغییر کرد.\n\n"
                    f"➖ مبلغ کسر شده: {amount:,} تومان\n"
                    f"💰 موجودی جدید: {new_balance:,} تومان"
                )

            )

        except Exception as error:

            print(
                "WALLET USER MESSAGE ERROR:",
                repr(error)
            )


        return True


    # =====================================================
    # CREATE ROOM
    # =====================================================

    if state == "room_name":

        context.user_data["room_name"] = text

        context.user_data["admin_state"] = "room_date"

        await update.message.reply_text(
            "📅 تاریخ روم را وارد کن:",
            reply_markup=cancel_menu()
        )

        return True


    if state == "room_date":

        context.user_data["room_date"] = text

        context.user_data["admin_state"] = "room_time"

        await update.message.reply_text(
            "⏰ ساعت روم را وارد کن:",
            reply_markup=cancel_menu()
        )

        return True


    if state == "room_time":

        context.user_data["room_time"] = text

        context.user_data["admin_state"] = "room_capacity"

        await update.message.reply_text(
            "👥 ظرفیت روم را وارد کن:",
            reply_markup=cancel_menu()
        )

        return True


    if state == "room_capacity":

        try:

            value = int(text)

            if value < 1:
                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ ظرفیت باید عدد باشد."
            )

            return True


        context.user_data["room_capacity"] = value

        context.user_data["admin_state"] = "entry_fee"

        await update.message.reply_text(
            "💰 ورودی روم را وارد کن:",
            reply_markup=cancel_menu()
        )

        return True


    if state == "entry_fee":

        try:

            value = int(text)

            if value < 0:
                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ مبلغ باید عدد باشد."
            )

            return True


        context.user_data["entry_fee"] = value

        context.user_data["admin_state"] = "kill_prize"

        await update.message.reply_text(
            "🔫 جایزه هر کیل را وارد کن:",
            reply_markup=cancel_menu()
        )

        return True


    if state == "kill_prize":

        try:

            value = int(text)

            if value < 0:
                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ مبلغ باید عدد باشد."
            )

            return True


        context.user_data["kill_prize"] = value

        context.user_data["admin_state"] = "first_prize"

        await update.message.reply_text(
            "🥇 جایزه تیم اول را وارد کن:",
            reply_markup=cancel_menu()
        )

        return True


    if state == "first_prize":

        try:

            value = int(text)

            if value < 0:
                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ مبلغ باید عدد باشد."
            )

            return True


        context.user_data["first_prize"] = value

        context.user_data["admin_state"] = "second_prize"

        await update.message.reply_text(
            "🥈 جایزه تیم دوم را وارد کن:",
            reply_markup=cancel_menu()
        )

        return True


    if state == "second_prize":

        try:

            value = int(text)

            if value < 0:
                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ مبلغ باید عدد باشد."
            )

            return True


        context.user_data["second_prize"] = value

        context.user_data["admin_state"] = "third_prize"

        await update.message.reply_text(
            "🥉 جایزه تیم سوم را وارد کن:",
            reply_markup=cancel_menu()
        )

        return True


    if state == "third_prize":

        try:

            value = int(text)

            if value < 0:
                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ مبلغ باید عدد باشد."
            )

            return True


        context.user_data["third_prize"] = value


        try:

            room_id = create_room(

                context.user_data["room_name"],
                context.user_data["room_date"],
                context.user_data["room_time"],
                context.user_data["room_capacity"],
                context.user_data["entry_fee"],
                context.user_data["kill_prize"],
                context.user_data["first_prize"],
                context.user_data["second_prize"],
                context.user_data["third_prize"]
            )

        except Exception as error:

            print(
                "CREATE ROOM ERROR:",
                repr(error)
            )

            await update.message.reply_text(
                "❌ خطا در ساخت روم."
            )

            return True


        data = dict(
            context.user_data
        )

        context.user_data.clear()


        await update.message.reply_text(

            "✅ روم با موفقیت ساخته شد!\n\n"

            f"🏠 نام روم: {data['room_name']}\n"
            f"📅 تاریخ: {data['room_date']}\n"
            f"⏰ ساعت: {data['room_time']}\n"
            f"👥 ظرفیت: {data['room_capacity']}\n"
            f"💰 ورودی: {data['entry_fee']:,} تومان\n"
            f"🔫 جایزه هر کیل: {data['kill_prize']:,} تومان\n"
            f"🥇 جایزه تیم اول: {data['first_prize']:,} تومان\n"
            f"🥈 جایزه تیم دوم: {data['second_prize']:,} تومان\n"
            f"🥉 جایزه تیم سوم: {data['third_prize']:,} تومان\n\n"
            f"🆔 شماره روم: {room_id}",

            reply_markup=admin_menu()
        )

        return True


    # =====================================================
    # EDIT NAME
    # =====================================================

    if state == "edit_name":

        room_id = context.user_data["edit_room_id"]

        update_room(
            room_id,
            name=text
        )

        context.user_data.clear()

        await update.message.reply_text(
            "✅ نام روم تغییر کرد.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "✏️ ویرایش دوباره",
                        callback_data=f"adm_edit_{room_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏠 مشخصات روم",
                        callback_data=f"adm_room_{room_id}"
                    )
                ]
            ])
        )

        return True


    # =====================================================
    # EDIT DATE
    # =====================================================

    if state == "edit_date":

        room_id = context.user_data["edit_room_id"]

        update_room(
            room_id,
            room_date=text
        )

        context.user_data.clear()

        await update.message.reply_text(
            "✅ تاریخ روم تغییر کرد.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "✏️ ویرایش دوباره",
                        callback_data=f"adm_edit_{room_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏠 مشخصات روم",
                        callback_data=f"adm_room_{room_id}"
                    )
                ]
            ])
        )

        return True


    # =====================================================
    # EDIT TIME
    # =====================================================

    if state == "edit_time":

        room_id = context.user_data["edit_room_id"]

        update_room(
            room_id,
            room_time=text
        )

        context.user_data.clear()

        await update.message.reply_text(
            "✅ ساعت روم تغییر کرد.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "✏️ ویرایش دوباره",
                        callback_data=f"adm_edit_{room_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏠 مشخصات روم",
                        callback_data=f"adm_room_{room_id}"
                    )
                ]
            ])
        )

        return True


    return False
