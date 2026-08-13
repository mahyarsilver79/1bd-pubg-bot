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
    delete_room_and_refund
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
# MENUS
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
# EDIT MENU
# =========================================================

def edit_room_menu(room_id):

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🏷 ویرایش نام",
                callback_data=f"adm_edit_name_{room_id}"
            )
        ],

        [
            InlineKeyboardButton(
                "📅 ویرایش تاریخ",
                callback_data=f"adm_edit_date_{room_id}"
            )
        ],

        [
            InlineKeyboardButton(
                "⏰ ویرایش ساعت",
                callback_data=f"adm_edit_time_{room_id}"
            )
        ],

        [
            InlineKeyboardButton(
                "🔙 مشخصات روم",
                callback_data=f"adm_room_{room_id}"
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

        context.user_data.clear()

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
            f"👥 ظرفیت: {room['capacity']} تیم\n"
            f"👤 تعداد تیم‌های ثبت‌نام‌شده: {team_count}\n"
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
                )
            ],

            [
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
                "👥 بازیکنان روم\n\n"
                f"🏠 {room['name']}\n\n"
                "❌ هنوز هیچ تیمی ثبت‌نام نکرده."
            )

        else:

            text = (
                "👥 بازیکنان روم\n\n"
                f"🏠 {room['name']}\n\n"
            )


            for index, team in enumerate(
                teams,
                start=1
            ):

                captain_username = team["captain_username"]

                if captain_username:

                    captain_text = f"@{captain_username}"

                else:

                    captain_text = str(
                        team["captain_telegram_id"]
                    )


                captain_first_name = (
                    team["captain_first_name"]
                    or "بدون نام"
                )


                text += (
                    f"🏆 تیم {index} — جایگاه {index}\n\n"

                    f"👑 کاپیتان: {captain_first_name}\n"
                    f"📱 ایدی تلگرام: {captain_text}\n"
                    f"🆔 Telegram ID: "
                    f"{team['captain_telegram_id']}\n\n"

                    f"1️⃣ {team['player1']}\n"
                    f"2️⃣ {team['player2']}\n"
                    f"3️⃣ {team['player3']}\n"
                    f"4️⃣ {team['player4']}\n\n"

                    "━━━━━━━━━━━━━━\n\n"
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
    # EDIT ROOM MENU
    # =====================================================

    if query.data.startswith("adm_edit_"):

        parts = query.data.split("_")

        # adm_edit_123
        if len(parts) == 3:

            room_id = int(parts[2])

            room = get_room(room_id)

            if not room:

                await query.edit_message_text(
                    "❌ روم پیدا نشد.",
                    reply_markup=back_menu()
                )

                return


            await query.edit_message_text(

                "✏️ ویرایش روم\n\n"

                f"🏠 {room['name']}\n"
                f"📅 {room['room_date']}\n"
                f"⏰ {room['room_time']}\n\n"

                "فقط گزینه‌ای که می‌خواهی تغییر کند را انتخاب کن:",

                reply_markup=edit_room_menu(room_id)
            )

            return


    # =====================================================
    # EDIT NAME
    # =====================================================

    if query.data.startswith("adm_edit_name_"):

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


        context.user_data.clear()

        context.user_data["admin_state"] = "edit_name"
        context.user_data["edit_room_id"] = room_id


        await query.edit_message_text(

            "🏷 ویرایش نام روم\n\n"

            f"نام فعلی:\n"
            f"{room['name']}\n\n"

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

        room = get_room(room_id)

        if not room:

            await query.edit_message_text(
                "❌ روم پیدا نشد.",
                reply_markup=back_menu()
            )

            return


        context.user_data.clear()

        context.user_data["admin_state"] = "edit_date"
        context.user_data["edit_room_id"] = room_id


        await query.edit_message_text(

            "📅 ویرایش تاریخ روم\n\n"

            f"تاریخ فعلی:\n"
            f"{room['room_date']}\n\n"

            "تاریخ جدید را وارد کن.\n\n"

            "مثال:\n"
            "شنبه ۲۵/۰۵",

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

        room = get_room(room_id)

        if not room:

            await query.edit_message_text(
                "❌ روم پیدا نشد.",
                reply_markup=back_menu()
            )

            return


        context.user_data.clear()

        context.user_data["admin_state"] = "edit_time"
        context.user_data["edit_room_id"] = room_id


        await query.edit_message_text(

            "⏰ ویرایش ساعت روم\n\n"

            f"ساعت فعلی:\n"
            f"{room['room_time']}\n\n"

            "ساعت جدید را وارد کن:",

            reply_markup=cancel_menu()
        )

        return


    # =====================================================
    # DELETE
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
    # DELETE CONFIRM
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


        captains = delete_room_and_refund(room_id)


        for telegram_id in captains:

            try:

                await context.bot.send_message(

                    chat_id=telegram_id,

                    text=(
                        "⚠️ اطلاعیه روم\n\n"

                        f"روم «{room['name']}» توسط مدیریت حذف شد.\n\n"

                        f"💰 مبلغ "
                        f"{room['entry_fee']:,} تومان "
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
            f"💰 مبلغ ورودی به "
            f"{len(captains)} کاپیتان برگشت داده شد.",

            reply_markup=back_menu()
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

    if not state:

        return False


    text = update.message.text.strip()


    # =====================================================
    # CREATE ROOM - NAME
    # =====================================================

    if state == "room_name":

        context.user_data["room_name"] = text

        context.user_data["admin_state"] = "room_date"

        await update.message.reply_text(

            "📅 تاریخ روم را وارد کن.\n\n"

            "مثال:\n"
            "شنبه ۲۵/۰۵",

            reply_markup=cancel_menu()
        )

        return True


    # =====================================================
    # CREATE ROOM - DATE
    # =====================================================

    if state == "room_date":

        context.user_data["room_date"] = text

        context.user_data["admin_state"] = "room_time"

        await update.message.reply_text(
            "⏰ ساعت روم را وارد کن:",
            reply_markup=cancel_menu()
        )

        return True


    # =====================================================
    # CREATE ROOM - TIME
    # =====================================================

    if state == "room_time":

        context.user_data["room_time"] = text

        context.user_data["admin_state"] = "room_capacity"

        await update.message.reply_text(
            "👥 ظرفیت روم را وارد کن:",
            reply_markup=cancel_menu()
        )

        return True


    # =====================================================
    # CREATE ROOM - CAPACITY
    # =====================================================

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


    # =====================================================
    # CREATE ROOM - ENTRY FEE
    # =====================================================

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


    # =====================================================
    # CREATE ROOM - KILL PRIZE
    # =====================================================

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


    # =====================================================
    # CREATE ROOM - FIRST PRIZE
    # =====================================================

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


    # =====================================================
    # CREATE ROOM - SECOND PRIZE
    # =====================================================

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


    # =====================================================
    # CREATE ROOM - THIRD PRIZE
    # =====================================================

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
            f"🔫 جایزه هر کیل: "
            f"{data['kill_prize']:,} تومان\n"
            f"🥇 جایزه تیم اول: "
            f"{data['first_prize']:,} تومان\n"
            f"🥈 جایزه تیم دوم: "
            f"{data['second_prize']:,} تومان\n"
            f"🥉 جایزه تیم سوم: "
            f"{data['third_prize']:,} تومان\n\n"
            f"🆔 شماره روم: {room_id}",

            reply_markup=admin_menu()
        )

        return True


    # =====================================================
    # EDIT NAME
    # =====================================================

    if state == "edit_name":

        room_id = context.user_data.get(
            "edit_room_id"
        )

        if not room_id:

            context.user_data.clear()

            await update.message.reply_text(
                "❌ خطا در شناسایی روم.",
                reply_markup=admin_menu()
            )

            return True


        room = get_room(room_id)

        if not room:

            context.user_data.clear()

            await update.message.reply_text(
                "❌ روم پیدا نشد.",
                reply_markup=admin_menu()
            )

            return True


        update_room(
            room_id,
            name=text
        )


        context.user_data.clear()


        await update.message.reply_text(

            "✅ نام روم با موفقیت تغییر کرد.\n\n"
            f"🏠 نام جدید: {text}",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🏠 مشخصات روم",
                        callback_data=f"adm_room_{room_id}"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "✏️ ویرایش دوباره",
                        callback_data=f"adm_edit_{room_id}"
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

        return True


    # =====================================================
    # EDIT DATE
    # =====================================================

    if state == "edit_date":

        room_id = context.user_data.get(
            "edit_room_id"
        )

        if not room_id:

            context.user_data.clear()

            await update.message.reply_text(
                "❌ خطا در شناسایی روم.",
                reply_markup=admin_menu()
            )

            return True


        room = get_room(room_id)

        if not room:

            context.user_data.clear()

            await update.message.reply_text(
                "❌ روم پیدا نشد.",
                reply_markup=admin_menu()
            )

            return True


        update_room(
            room_id,
            room_date=text
        )


        context.user_data.clear()


        await update.message.reply_text(

            "✅ تاریخ روم با موفقیت تغییر کرد.\n\n"
            f"📅 تاریخ جدید: {text}",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🏠 مشخصات روم",
                        callback_data=f"adm_room_{room_id}"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "✏️ ویرایش دوباره",
                        callback_data=f"adm_edit_{room_id}"
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

        return True


    # =====================================================
    # EDIT TIME
    # =====================================================

    if state == "edit_time":

        room_id = context.user_data.get(
            "edit_room_id"
        )

        if not room_id:

            context.user_data.clear()

            await update.message.reply_text(
                "❌ خطا در شناسایی روم.",
                reply_markup=admin_menu()
            )

            return True


        room = get_room(room_id)

        if not room:

            context.user_data.clear()

            await update.message.reply_text(
                "❌ روم پیدا نشد.",
                reply_markup=admin_menu()
            )

            return True


        update_room(
            room_id,
            room_time=text
        )


        context.user_data.clear()


        await update.message.reply_text(

            "✅ ساعت روم با موفقیت تغییر کرد.\n\n"
            f"⏰ ساعت جدید: {text}",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🏠 مشخصات روم",
                        callback_data=f"adm_room_{room_id}"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "✏️ ویرایش دوباره",
                        callback_data=f"adm_edit_{room_id}"
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

        return True


    return False
