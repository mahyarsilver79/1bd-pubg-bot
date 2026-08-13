import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import (
    create_room,
    get_rooms,
    get_room,
    update_room,
    delete_room,
    reset_room,
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

    text = update.message.text.strip()


    # =====================================================
    # ROOM NAME
    # =====================================================

    if state == "room_name":

        if not text:

            await update.message.reply_text(
                "❌ اسم روم نمی‌تواند خالی باشد."
            )

            return True

        context.user_data[
            "room_name"
        ] = text

        context.user_data[
            "admin_state"
        ] = "room_date"

        await update.message.reply_text(
            "📅 تاریخ روم را وارد کن:",
            reply_markup=cancel_menu()
        )

        return True


    # =====================================================
    # ROOM DATE
    # =====================================================

    if state == "room_date":

        if not text:

            await update.message.reply_text(
                "❌ تاریخ نمی‌تواند خالی باشد."
            )

            return True

        context.user_data[
            "room_date"
        ] = text

        context.user_data[
            "admin_state"
        ] = "room_time"

        await update.message.reply_text(
            "⏰ ساعت روم را وارد کن:",
            reply_markup=cancel_menu()
        )

        return True


    # =====================================================
    # ROOM TIME
    # =====================================================

    if state == "room_time":

        if not text:

            await update.message.reply_text(
                "❌ ساعت نمی‌تواند خالی باشد."
            )

            return True

        context.user_data[
            "room_time"
        ] = text

        context.user_data[
            "admin_state"
        ] = "room_capacity"

        await update.message.reply_text(
            "👥 ظرفیت روم را وارد کن:",
            reply_markup=cancel_menu()
        )

        return True


    # =====================================================
    # CAPACITY
    # =====================================================

    if state == "room_capacity":

        try:

            capacity = int(text)

            if capacity < 1:

                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ ظرفیت باید یک عدد معتبر باشد."
            )

            return True

        context.user_data[
            "room_capacity"
        ] = capacity

        context.user_data[
            "admin_state"
        ] = "entry_fee"

        await update.message.reply_text(
            "💰 ورودی روم را وارد کن:",
            reply_markup=cancel_menu()
        )

        return True


    # =====================================================
    # ENTRY FEE
    # =====================================================

    if state == "entry_fee":

        try:

            entry_fee = int(text)

            if entry_fee < 0:

                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ مبلغ باید یک عدد معتبر باشد."
            )

            return True

        context.user_data[
            "entry_fee"
        ] = entry_fee

        context.user_data[
            "admin_state"
        ] = "kill_prize"

        await update.message.reply_text(
            "🔫 جایزه هر کیل را وارد کن:",
            reply_markup=cancel_menu()
        )

        return True


    # =====================================================
    # KILL PRIZE
    # =====================================================

    if state == "kill_prize":

        try:

            kill_prize = int(text)

            if kill_prize < 0:

                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ مبلغ باید یک عدد معتبر باشد."
            )

            return True

        context.user_data[
            "kill_prize"
        ] = kill_prize

        context.user_data[
            "admin_state"
        ] = "first_prize"

        await update.message.reply_text(
            "🥇 جایزه اول را وارد کن:",
            reply_markup=cancel_menu()
        )

        return True


    # =====================================================
    # FIRST PRIZE
    # =====================================================

    if state == "first_prize":

        try:

            first_prize = int(text)

            if first_prize < 0:

                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ مبلغ باید یک عدد معتبر باشد."
            )

            return True

        context.user_data[
            "first_prize"
        ] = first_prize

        context.user_data[
            "admin_state"
        ] = "second_prize"

        await update.message.reply_text(
            "🥈 جایزه دوم را وارد کن:",
            reply_markup=cancel_menu()
        )

        return True


    # =====================================================
    # SECOND PRIZE
    # =====================================================

    if state == "second_prize":

        try:

            second_prize = int(text)

            if second_prize < 0:

                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ مبلغ باید یک عدد معتبر باشد."
            )

            return True

        context.user_data[
            "second_prize"
        ] = second_prize

        context.user_data[
            "admin_state"
        ] = "third_prize"

        await update.message.reply_text(
            "🥉 جایزه سوم را وارد کن:",
            reply_markup=cancel_menu()
        )

        return True


    # =====================================================
    # THIRD PRIZE
    # =====================================================

    if state == "third_prize":

        try:

            third_prize = int(text)

            if third_prize < 0:

                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ مبلغ باید یک عدد معتبر باشد."
            )

            return True

        context.user_data[
            "third_prize"
        ] = third_prize


        # =================================================
        # SAVE ROOM
        # =================================================

        try:

            room_id = create_room(

                name=context.user_data[
                    "room_name"
                ],

                room_date=context.user_data[
                    "room_date"
                ],

                room_time=context.user_data[
                    "room_time"
                ],

                capacity=context.user_data[
                    "room_capacity"
                ],

                entry_fee=context.user_data[
                    "entry_fee"
                ],

                kill_prize=context.user_data[
                    "kill_prize"
                ],

                first_prize=context.user_data[
                    "first_prize"
                ],

                second_prize=context.user_data[
                    "second_prize"
                ],

                third_prize=context.user_data[
                    "third_prize"
                ],
            )


        except Exception as error:

            print(
                "CREATE ROOM ERROR:",
                repr(error)
            )

            await update.message.reply_text(
                "❌ هنگام ساخت روم خطایی رخ داد."
            )

            return True


        room_name = context.user_data[
            "room_name"
        ]

        room_date = context.user_data[
            "room_date"
        ]

        room_time = context.user_data[
            "room_time"
        ]

        capacity = context.user_data[
            "room_capacity"
        ]

        entry_fee = context.user_data[
            "entry_fee"
        ]

        kill_prize = context.user_data[
            "kill_prize"
        ]

        first_prize = context.user_data[
            "first_prize"
        ]

        second_prize = context.user_data[
            "second_prize"
        ]

        third_prize = context.user_data[
            "third_prize"
        ]


        context.user_data.clear()


        # =================================================
        # SUCCESS
        # =================================================

        await update.message.reply_text(

            "✅ روم با موفقیت ساخته شد!\n\n"

            f"🏠 {room_name}\n"
            f"📅 تاریخ: {room_date}\n"
            f"⏰ ساعت: {room_time}\n"
            f"👥 ظرفیت: {capacity}\n"
            f"💰 ورودی: {entry_fee:,}\n"
            f"🔫 جایزه کیل: {kill_prize:,}\n"
            f"🥇 جایزه اول: {first_prize:,}\n"
            f"🥈 جایزه دوم: {second_prize:,}\n"
            f"🥉 جایزه سوم: {third_prize:,}\n\n"

            f"🆔 شماره روم: {room_id}",

            reply_markup=admin_menu()
        )

        return True


    return False
