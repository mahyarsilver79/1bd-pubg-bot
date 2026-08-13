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
    get_withdrawals,
    get_withdrawal,
    complete_withdrawal,
    get_user,
    add_wallet,
    subtract_wallet,
)


def is_admin(user_id):
    admin_id = os.getenv("ADMIN_ID")
    return bool(admin_id) and str(user_id) == str(admin_id)


def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🏠 ساخت روم",
            callback_data="adm_create_room"
        )],
        [InlineKeyboardButton(
            "📋 لیست روم‌ها",
            callback_data="adm_rooms"
        )],
        [InlineKeyboardButton(
            "💸 برداشت‌ها",
            callback_data="adm_withdrawals"
        )],
        [InlineKeyboardButton(
            "👤 مدیریت کاربران",
            callback_data="adm_users"
        )],
    ])


def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🔙 پنل مدیریت",
            callback_data="adm_back"
        )]
    ])


def cancel_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "❌ لغو",
            callback_data="adm_cancel"
        )]
    ])


async def admin_panel(update, context):

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


async def admin_button_handler(update, context):

    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text(
            "⛔ دسترسی غیرمجاز."
        )
        return

    data = query.data

    # =====================================================
    # CREATE ROOM
    # =====================================================

    if data == "adm_create_room":

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

    if data == "adm_rooms":

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
                    f"{room['room_date']} | "
                    f"{room['room_time']}",
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

    if data.startswith("adm_room_"):

        room_id = int(data.split("_")[2])
        room = get_room(room_id)

        if not room:
            await query.edit_message_text(
                "❌ روم پیدا نشد.",
                reply_markup=back_menu()
            )
            return

        count = get_room_team_count(room_id)

        status = (
            "🟢 فعال"
            if room["status"] == "open"
            else "🔴 بسته / تکمیل"
        )

        text = (
            "🏠 مشخصات روم\n\n"
            f"🏷 نام: {room['name']}\n"
            f"📅 تاریخ: {room['room_date']}\n"
            f"⏰ ساعت: {room['room_time']}\n"
            f"👥 ظرفیت: {room['capacity']}\n"
            f"👤 تیم‌ها: {count}\n\n"
            f"💰 ورودی: {room['entry_fee']:,} تومان\n"
            f"🔫 جایزه هر کیل: {room['kill_prize']:,} تومان\n"
            f"🥇 تیم اول: {room['first_prize']:,} تومان\n"
            f"🥈 تیم دوم: {room['second_prize']:,} تومان\n"
            f"🥉 تیم سوم: {room['third_prize']:,} تومان\n\n"
            f"📌 وضعیت: {status}\n"
            f"🆔 شماره روم: {room['id']}"
        )

        keyboard = [
            [InlineKeyboardButton(
                "👥 بازیکنان روم",
                callback_data=f"adm_players_{room_id}"
            )],
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
            [InlineKeyboardButton(
                "🔙 لیست روم‌ها",
                callback_data="adm_rooms"
            )],
            [InlineKeyboardButton(
                "🏠 پنل مدیریت",
                callback_data="adm_back"
            )]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # =====================================================
    # PLAYERS
    # =====================================================

    if data.startswith("adm_players_"):

        room_id = int(data.split("_")[2])
        room = get_room(room_id)

        teams = get_room_teams(room_id)

        if not teams:
            text = (
                f"👥 بازیکنان روم\n\n"
                f"🏠 {room['name']}\n\n"
                "❌ هنوز تیمی ثبت‌نام نکرده."
            )
        else:

            text = (
                f"👥 بازیکنان روم\n\n"
                f"🏠 {room['name']}\n\n"
            )

            for index, team in enumerate(teams, start=1):

                username = team["captain_username"]

                if username:
                    captain = f"@{username}"
                else:
                    captain = str(
                        team["captain_telegram_id"]
                    )

                text += (
                    f"🏆 تیم {index} — جایگاه {index}\n"
                    f"👑 کاپیتان: {captain}\n"
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
                [InlineKeyboardButton(
                    "🔙 مشخصات روم",
                    callback_data=f"adm_room_{room_id}"
                )]
            ])
        )
        return

    # =====================================================
    # DELETE
    # =====================================================

    if data.startswith("adm_delete_"):

        room_id = int(data.split("_")[2])
        room = get_room(room_id)

        if not room:
            await query.edit_message_text(
                "❌ روم پیدا نشد.",
                reply_markup=back_menu()
            )
            return

        count = get_room_team_count(room_id)

        await query.edit_message_text(
            "⚠️ حذف روم\n\n"
            f"🏠 {room['name']}\n"
            f"👥 تیم‌های ثبت‌شده: {count}\n\n"
            "با حذف روم، مبلغ ورودی تمام کاپیتان‌ها "
            "به کیف پولشان برمی‌گردد و به آنها اطلاع داده می‌شود.\n\n"
            "آیا مطمئنی؟",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "✅ بله، حذف کن",
                    callback_data=f"adm_delete_confirm_{room_id}"
                )],
                [InlineKeyboardButton(
                    "❌ انصراف",
                    callback_data=f"adm_room_{room_id}"
                )]
            ])
        )
        return

    if data.startswith("adm_delete_confirm_"):

        room_id = int(data.split("_")[3])
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
                        f"💰 مبلغ {room['entry_fee']:,} تومان "
                        "به کیف پول شما برگشت داده شد."
                    )
                )
            except Exception as error:
                print("DELETE ROOM MESSAGE ERROR:", repr(error))

        await query.edit_message_text(
            "✅ روم حذف شد.\n\n"
            f"🏠 {room['name']}\n"
            f"💰 بازگشت وجه برای {len(captains)} تیم انجام شد.",
            reply_markup=back_menu()
        )
        return

    # =====================================================
    # EDIT ROOM
    # =====================================================

    if data.startswith("adm_edit_"):

        room_id = int(data.split("_")[2])
        room = get_room(room_id)

        if not room:
            await query.edit_message_text(
                "❌ روم پیدا نشد.",
                reply_markup=back_menu()
            )
            return

        await query.edit_message_text(
            f"✏️ ویرایش روم «{room['name']}»\n\n"
            "فقط همان بخشی که می‌خواهی تغییر کند انتخاب کن:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "🏷 تغییر اسم",
                    callback_data=f"adm_editname_{room_id}"
                )],
                [InlineKeyboardButton(
                    "📅 تغییر تاریخ",
                    callback_data=f"adm_editdate_{room_id}"
                )],
                [InlineKeyboardButton(
                    "⏰ تغییر ساعت",
                    callback_data=f"adm_edittime_{room_id}"
                )],
                [InlineKeyboardButton(
                    "🔙 مشخصات روم",
                    callback_data=f"adm_room_{room_id}"
                )]
            ])
        )
        return

    if data.startswith("adm_editname_"):
        room_id = int(data.split("_")[1])

        context.user_data.clear()
        context.user_data["admin_state"] = "edit_name"
        context.user_data["edit_room_id"] = room_id

        await query.edit_message_text(
            "🏷 اسم جدید روم را وارد کن:",
            reply_markup=cancel_menu()
        )
        return

    if data.startswith("adm_editdate_"):
        room_id = int(data.split("_")[1])

        context.user_data.clear()
        context.user_data["admin_state"] = "edit_date"
        context.user_data["edit_room_id"] = room_id

        await query.edit_message_text(
            "📅 تاریخ جدید را دقیقاً با همین فرمت وارد کن:\n\n"
            "مثال: شنبه ۲۵/۰۵",
            reply_markup=cancel_menu()
        )
        return

    if data.startswith("adm_edittime_"):
        room_id = int(data.split("_")[1])

        context.user_data.clear()
        context.user_data["admin_state"] = "edit_time"
        context.user_data["edit_room_id"] = room_id

        await query.edit_message_text(
            "⏰ ساعت جدید را وارد کن:\n\n"
            "مثال: ۲۳:۰۰",
            reply_markup=cancel_menu()
        )
        return

    # =====================================================
    # WITHDRAWALS
    # =====================================================

    if data == "adm_withdrawals":

        rows = get_withdrawals("pending")

        if not rows:
            await query.edit_message_text(
                "💸 برداشت‌ها\n\n"
                "❌ درخواست در انتظار پرداختی وجود ندارد.",
                reply_markup=back_menu()
            )
            return

        keyboard = []

        for row in rows:
            name = row["username"] or row["first_name"] or str(
                row["telegram_id"]
            )

            keyboard.append([
                InlineKeyboardButton(
                    f"💸 {name} | {row['amount']:,} تومان",
                    callback_data=f"adm_withdraw_{row['id']}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                "🔙 پنل مدیریت",
                callback_data="adm_back"
            )
        ])

        await query.edit_message_text(
            "💸 درخواست‌های برداشت\n\n"
            "درخواست موردنظر را انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("adm_withdraw_"):

        withdrawal_id = int(data.split("_")[2])
        row = get_withdrawal(withdrawal_id)

        if not row:
            await query.edit_message_text(
                "❌ درخواست پیدا نشد.",
                reply_markup=back_menu()
            )
            return

        name = row["username"] or row["first_name"] or "-"

        await query.edit_message_text(
            "💸 درخواست برداشت\n\n"
            f"👤 کاربر: {name}\n"
            f"🆔 Telegram ID: {row['telegram_id']}\n"
            f"💰 موجودی فعلی: {row['wallet']:,} تومان\n"
            f"💸 مبلغ درخواست: {row['amount']:,} تومان\n"
            f"🏦 حساب: {row['bank_account']}\n"
            f"⏳ وضعیت: {row['status']}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "💳 پرداخت شد",
                    callback_data=f"adm_paywithdraw_{withdrawal_id}"
                )],
                [InlineKeyboardButton(
                    "🔙 برداشت‌ها",
                    callback_data="adm_withdrawals"
                )]
            ])
        )
        return

    if data.startswith("adm_paywithdraw_"):

        withdrawal_id = int(data.split("_")[2])

        context.user_data.clear()
        context.user_data["admin_state"] = "withdraw_receipt"
        context.user_data["withdrawal_id"] = withdrawal_id

        await query.edit_message_text(
            "💳 پرداخت را انجام دادی.\n\n"
            "حالا عکس رسید یا مشخصات رسید را ارسال کن:"
        )
        return

    if data == "adm_users":

        context.user_data.clear()
        context.user_data["admin_state"] = "user_search"

        await query.edit_message_text(
            "👤 مدیریت کاربران\n\n"
            "Telegram ID کاربر را وارد کن:",
            reply_markup=cancel_menu()
        )
        return

    # =====================================================
    # ADMIN BACK / CANCEL
    # =====================================================

    if data == "adm_back":

        context.user_data.clear()

        await query.edit_message_text(
            "👑 پنل مدیریت\n\n"
            "یک گزینه را انتخاب کن:",
            reply_markup=admin_menu()
        )
        return

    if data == "adm_cancel":

        context.user_data.clear()

        await query.edit_message_text(
            "👑 پنل مدیریت\n\n"
            "یک گزینه را انتخاب کن:",
            reply_markup=admin_menu()
        )
        return


async def handle_admin_message(update, context):

    if not is_admin(update.effective_user.id):
        return False

    state = context.user_data.get("admin_state")

    if not state:
        return False

    # =====================================================
    # CREATE ROOM
    # =====================================================

    if state == "room_name":

        context.user_data["room_name"] = update.message.text.strip()
        context.user_data["admin_state"] = "room_date"

        await update.message.reply_text(
            "📅 تاریخ روم را وارد کن.\n\n"
            "فرمت:\n"
            "شنبه ۲۵/۰۵\n\n"
            "روز هفته را هم حتماً بنویس.",
            reply_markup=cancel_menu()
        )
        return True

    if state == "room_date":

        value = update.message.text.strip()

        if not value:
            await update.message.reply_text(
                "❌ تاریخ نمی‌تواند خالی باشد."
            )
            return True

        context.user_data["room_date"] = value
        context.user_data["admin_state"] = "room_time"

        await update.message.reply_text(
            "⏰ ساعت روم را وارد کن.\n\n"
            "مثال: ۲۳:۰۰",
            reply_markup=cancel_menu()
        )
        return True

    if state == "room_time":

        value = update.message.text.strip()

        context.user_data["room_time"] = value
        context.user_data["admin_state"] = "room_capacity"

        await update.message.reply_text(
            "👥 ظرفیت روم را وارد کن:",
            reply_markup=cancel_menu()
        )
        return True

    if state == "room_capacity":

        try:
            value = int(
                update.message.text.replace(",", "").replace("٬", "")
            )

            if value < 1:
                raise ValueError

        except ValueError:
            await update.message.reply_text(
                "❌ ظرفیت باید عدد مثبت باشد."
            )
            return True

        context.user_data["room_capacity"] = value
        context.user_data["admin_state"] = "entry_fee"

        await update.message.reply_text(
            "💰 مبلغ ورودی روم را به تومان وارد کن:",
            reply_markup=cancel_menu()
        )
        return True

    if state == "entry_fee":

        try:
            value = int(
                update.message.text.replace(",", "").replace("٬", "")
            )

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
            "🔫 مبلغ جایزه هر کیل را به تومان وارد کن:",
            reply_markup=cancel_menu()
        )
        return True

    if state == "kill_prize":

        try:
            value = int(
                update.message.text.replace(",", "").replace("٬", "")
            )

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
            "🥇 جایزه تیم اول را به تومان وارد کن:",
            reply_markup=cancel_menu()
        )
        return True

    if state == "first_prize":

        try:
            value = int(
                update.message.text.replace(",", "").replace("٬", "")
            )

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
            "🥈 جایزه تیم دوم را به تومان وارد کن:",
            reply_markup=cancel_menu()
        )
        return True

    if state == "second_prize":

        try:
            value = int(
                update.message.text.replace(",", "").replace("٬", "")
            )

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
            "🥉 جایزه تیم سوم را به تومان وارد کن:",
            reply_markup=cancel_menu()
        )
        return True

    if state == "third_prize":

        try:
            value = int(
                update.message.text.replace(",", "").replace("٬", "")
            )

            if value < 0:
                raise ValueError

        except ValueError:
            await update.message.reply_text(
                "❌ مبلغ باید عدد باشد."
            )
            return True

        context.user_data["third_prize"] = value

        data = dict(context.user_data)

        try:
            room_id = create_room(
                data["room_name"],
                data["room_date"],
                data["room_time"],
                data["room_capacity"],
                data["entry_fee"],
                data["kill_prize"],
                data["first_prize"],
                data["second_prize"],
                data["third_prize"]
            )
        except Exception as error:
            print("CREATE ROOM ERROR:", repr(error))

            await update.message.reply_text(
                "❌ خطا در ساخت روم."
            )
            return True

        context.user_data.clear()

        await update.message.reply_text(
            "✅ روم با موفقیت ساخته شد!\n\n"
            f"🏠 {data['room_name']}\n"
            f"📅 {data['room_date']}\n"
            f"⏰ {data['room_time']}\n"
            f"👥 ظرفیت: {data['room_capacity']}\n"
            f"💰 ورودی: {data['entry_fee']:,} تومان\n"
            f"🔫 جایزه هر کیل: {data['kill_prize']:,} تومان\n"
            f"🥇 تیم اول: {data['first_prize']:,} تومان\n"
            f"🥈 تیم دوم: {data['second_prize']:,} تومان\n"
            f"🥉 تیم سوم: {data['third_prize']:,} تومان\n\n"
            f"🆔 شماره روم: {room_id}",
            reply_markup=admin_menu()
        )
        return True

    # =====================================================
    # EDIT ROOM
    # =====================================================

    if state == "edit_name":

        room_id = context.user_data["edit_room_id"]

        update_room(
            room_id,
            name=update.message.text.strip()
        )

        context.user_data.clear()

        await update.message.reply_text(
            "✅ اسم روم تغییر کرد.",
            reply_markup=admin_menu()
        )
        return True

    if state == "edit_date":

        room_id = context.user_data["edit_room_id"]

        update_room(
            room_id,
            room_date=update.message.text.strip()
        )

        context.user_data.clear()

        await update.message.reply_text(
            "✅ تاریخ روم تغییر کرد.",
            reply_markup=admin_menu()
        )
        return True

    if state == "edit_time":

        room_id = context.user_data["edit_room_id"]

        update_room(
            room_id,
            room_time=update.message.text.strip()
        )

        context.user_data.clear()

        await update.message.reply_text(
            "✅ ساعت روم تغییر کرد.",
            reply_markup=admin_menu()
        )
        return True

    # =====================================================
    # WITHDRAW RECEIPT
    # =====================================================

    if state == "withdraw_receipt":

        withdrawal_id = context.user_data["withdrawal_id"]

        if update.message.photo:

            photo = update.message.photo[-1]

            success, result = complete_withdrawal(
                withdrawal_id,
                "photo",
                photo.file_id
            )

            receipt_type = "photo"
            receipt_data = photo.file_id

        else:

            value = update.message.text.strip()

            success, result = complete_withdrawal(
                withdrawal_id,
                "text",
                value
            )

            receipt_type = "text"
            receipt_data = value

        if not success:

            messages = {
                "already_processed":
                    "❌ این درخواست قبلاً پرداخت شده.",
                "insufficient_wallet":
                    "❌ موجودی کاربر برای کسر مبلغ کافی نیست.",
                "not_found":
                    "❌ درخواست پیدا نشد."
            }

            await update.message.reply_text(
                messages.get(
                    result,
                    "❌ پرداخت انجام نشد."
                )
            )
            return True

        context.user_data.clear()

        withdrawal = get_withdrawal(withdrawal_id)

        try:

            if receipt_type == "photo":
                await context.bot.send_photo(
                    chat_id=result,
                    photo=receipt_data,
                    caption=(
                        "✅ برداشت شما پرداخت شد.\n\n"
                        f"💰 مبلغ: {withdrawal['amount']:,} تومان\n"
                        "🧾 رسید پرداخت در پیام ارسال شده."
                    )
                )
            else:
                await context.bot.send_message(
                    chat_id=result,
                    text=(
                        "✅ برداشت شما پرداخت شد.\n\n"
                        f"💰 مبلغ: {withdrawal['amount']:,} تومان\n\n"
                        f"🧾 رسید:\n{receipt_data}"
                    )
                )

        except Exception as error:
            print("SEND RECEIPT ERROR:", repr(error))

        await update.message.reply_text(
            "✅ پرداخت ثبت شد.\n"
            "💰 مبلغ از کیف پول کاربر کسر شد.\n"
            "🧾 رسید برای کاربر ارسال شد.",
            reply_markup=admin_menu()
        )
        return True

    # =====================================================
    # USER SEARCH
    # =====================================================

    if state == "user_search":

        try:
            telegram_id = int(
                update.message.text.strip()
            )
        except ValueError:
            await update.message.reply_text(
                "❌ Telegram ID باید عدد باشد."
            )
            return True

        user = get_user(telegram_id)

        if not user:
            await update.message.reply_text(
                "❌ کاربر پیدا نشد.",
                reply_markup=admin_menu()
            )
            context.user_data.clear()
            return True

        context.user_data.clear()

        username = (
            f"@{user['username']}"
            if user["username"]
            else "-"
        )

        await update.message.reply_text(
            "👤 اطلاعات کاربر\n\n"
            f"👤 نام: {user['first_name'] or '-'}\n"
            f"🔗 Username: {username}\n"
            f"🆔 Telegram ID: {user['telegram_id']}\n"
            f"💰 موجودی: {user['wallet']:,} تومان\n"
            f"🏦 حساب: {user['bank_account'] or 'ثبت نشده'}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "➕ افزایش موجودی",
                    callback_data=f"adm_addwallet_{user['telegram_id']}"
                )],
                [InlineKeyboardButton(
                    "➖ کاهش موجودی",
                    callback_data=f"adm_subwallet_{user['telegram_id']}"
                )],
                [InlineKeyboardButton(
                    "🔙 پنل مدیریت",
                    callback_data="adm_back"
                )]
            ])
        )
        return True

    # =====================================================
    # WALLET ADMIN AMOUNT
    # =====================================================

    if state == "add_wallet":

        telegram_id = context.user_data["wallet_user"]
        amount_text = update.message.text.strip()

        try:
            amount = int(
                amount_text.replace(",", "").replace("٬", "")
            )
            if amount <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text(
                "❌ مبلغ باید عدد مثبت باشد."
            )
            return True

        add_wallet(
            telegram_id,
            amount,
            "Admin wallet increase"
        )

        context.user_data.clear()

        await update.message.reply_text(
            "✅ موجودی افزایش پیدا کرد.",
            reply_markup=admin_menu()
        )
        return True

    if state == "sub_wallet":

        telegram_id = context.user_data["wallet_user"]
        amount_text = update.message.text.strip()

        try:
            amount = int(
                amount_text.replace(",", "").replace("٬", "")
            )
            if amount <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text(
                "❌ مبلغ باید عدد مثبت باشد."
            )
            return True

        success = subtract_wallet(
            telegram_id,
            amount,
            "Admin wallet decrease"
        )

        if not success:
            await update.message.reply_text(
                "❌ موجودی کافی نیست."
            )
            return True

        context.user_data.clear()

        await update.message.reply_text(
            "✅ موجودی کم شد.",
            reply_markup=admin_menu()
        )
        return True

    return False
