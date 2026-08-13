import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import (
    create_match,
    create_room,
    get_matches,
    get_match_rooms,
    get_match_financials,
)


def is_admin(user_id):
    admin_id = os.getenv("ADMIN_ID")

    if not admin_id:
        return False

    return str(user_id) == str(admin_id)


def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🎮 ساخت مسابقه",
            callback_data="adm_create_match"
        )],
        [InlineKeyboardButton(
            "🏠 ساخت روم",
            callback_data="adm_create_room"
        )],
        [InlineKeyboardButton(
            "📋 لیست مسابقات",
            callback_data="adm_matches"
        )],
    ])


def cancel_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "❌ لغو",
            callback_data="adm_cancel"
        )]
    ])


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ دسترسی غیرمجاز.")
        return

    context.user_data.clear()

    await update.message.reply_text(
        "👑 پنل مدیریت 1BD PUBG\n\n"
        "یک گزینه را انتخاب کن:",
        reply_markup=admin_menu()
    )


async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("⛔ دسترسی غیرمجاز.")
        return

    # =====================================================
    # شروع ساخت مسابقه
    # =====================================================

    if query.data == "adm_create_match":

        context.user_data.clear()

        context.user_data["admin_state"] = "match_name"

        await query.edit_message_text(
            "🎮 ساخت مسابقه\n\n"
            "📝 اسم مسابقه را وارد کن:\n\n"
            "مثلاً:\n"
            "PUBG NIGHT\n"
            "مسابقه جمعه\n"
            "یا حتی فقط: 1",
            reply_markup=cancel_menu()
        )

        return

    # =====================================================
    # ساخت روم
    # =====================================================

    if query.data == "adm_create_room":

        matches = get_matches()

        if not matches:

            await query.edit_message_text(
                "❌ هنوز هیچ مسابقه‌ای ساخته نشده.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="adm_back"
                    )]
                ])
            )

            return

        keyboard = []

        for match in matches:

            keyboard.append([
                InlineKeyboardButton(
                    f"🎮 {match['name']} | ID: {match['id']}",
                    callback_data=f"adm_room_{match['id']}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                "🔙 پنل مدیریت",
                callback_data="adm_back"
            )
        ])

        await query.edit_message_text(
            "🏠 ساخت روم\n\n"
            "مسابقه‌ای که می‌خواهی برایش روم بسازی انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # =====================================================
    # انتخاب مسابقه برای ساخت روم
    # =====================================================

    if query.data.startswith("adm_room_"):

        match_id = int(query.data.split("_")[2])

        context.user_data.clear()

        context.user_data["admin_state"] = "room_name"
        context.user_data["match_id"] = match_id

        await query.edit_message_text(
            "🏠 ساخت روم\n\n"
            "📝 اسم روم را وارد کن:",
            reply_markup=cancel_menu()
        )

        return

    # =====================================================
    # لیست مسابقات
    # =====================================================

    if query.data == "adm_matches":

        matches = get_matches()

        if not matches:

            text = "📋 هنوز هیچ مسابقه‌ای ساخته نشده."

        else:

            text = "📋 مسابقات\n\n"

            for match in matches:

                financial = get_match_financials(
                    match["id"]
                )

                rooms = get_match_rooms(
                    match["id"]
                )

                text += (
                    f"🏆 {match['name']}\n"
                    f"📅 {match['match_date'] or 'نامشخص'}\n"
                    f"⏰ {match['match_time'] or 'نامشخص'}\n"
                    f"🏠 تعداد روم: {len(rooms)}\n"
                    f"💰 درآمد: {financial['revenue']:,}\n"
                    f"🎁 جوایز: {financial['prizes']:,}\n"
                    f"📊 سود/مانده: {financial['profit']:,}\n\n"
                )

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "➕ ساخت مسابقه",
                    callback_data="adm_create_match"
                )],
                [InlineKeyboardButton(
                    "🔙 پنل مدیریت",
                    callback_data="adm_back"
                )]
            ])
        )

        return

    # =====================================================
    # لغو
    # =====================================================

    if query.data == "adm_cancel":

        context.user_data.clear()

        await query.edit_message_text(
            "👑 پنل مدیریت 1BD PUBG\n\n"
            "یک گزینه را انتخاب کن:",
            reply_markup=admin_menu()
        )

        return

    # =====================================================
    # بازگشت
    # =====================================================

    if query.data == "adm_back":

        context.user_data.clear()

        await query.edit_message_text(
            "👑 پنل مدیریت 1BD PUBG\n\n"
            "یک گزینه را انتخاب کن:",
            reply_markup=admin_menu()
        )

        return


async def handle_admin_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(update.effective_user.id):
        return False

    state = context.user_data.get("admin_state")

    text = update.message.text.strip()

    # =====================================================
    # اسم مسابقه
    # =====================================================

    if state == "match_name":

        context.user_data["match_name"] = text

        context.user_data["admin_state"] = "match_date"

        await update.message.reply_text(
            "📅 تاریخ مسابقه را وارد کن:\n\n"
            "مثال:\n"
            "1405/05/25"
        )

        return True

    # =====================================================
    # تاریخ
    # =====================================================

    if state == "match_date":

        context.user_data["match_date"] = text

        context.user_data["admin_state"] = "match_time"

        await update.message.reply_text(
            "⏰ ساعت شروع مسابقه را وارد کن:\n\n"
            "مثال:\n"
            "21:00"
        )

        return True

    # =====================================================
    # ساعت
    # =====================================================

    if state == "match_time":

        context.user_data["match_time"] = text

        context.user_data["admin_state"] = "room_count"

        await update.message.reply_text(
            "🏠 چند روم برای این مسابقه می‌خواهی؟\n\n"
            "مثلاً:\n"
            "1\n"
            "2\n"
            "4"
        )

        return True

    # =====================================================
    # تعداد روم
    # =====================================================

    if state == "room_count":

        try:

            room_count = int(text)

            if room_count < 1:
                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ تعداد روم باید یک عدد حداقل 1 باشد."
            )

            return True

        context.user_data["room_count"] = room_count
        context.user_data["current_room"] = 1
        context.user_data["rooms"] = []

        context.user_data["admin_state"] = "room_name"

        await update.message.reply_text(
            f"🏠 روم 1 از {room_count}\n\n"
            "📝 اسم این روم را وارد کن:"
        )

        return True

    # =====================================================
    # اسم روم
    # =====================================================

    if state == "room_name":

        context.user_data["current_room_name"] = text

        context.user_data["admin_state"] = "room_capacity"

        await update.message.reply_text(
            "👥 ظرفیت این روم چند نفر باشد؟\n\n"
            "مثال:\n"
            "64"
        )

        return True

    # =====================================================
    # ظرفیت
    # =====================================================

    if state == "room_capacity":

        try:

            capacity = int(text)

            if capacity < 1:
                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ ظرفیت باید عدد باشد."
            )

            return True

        context.user_data["current_capacity"] = capacity

        context.user_data["admin_state"] = "entry_fee"

        await update.message.reply_text(
            "💰 ورودی این روم چقدر باشد؟\n\n"
            "مثال:\n"
            "50000\n"
            "100000"
        )

        return True

    # =====================================================
    # ورودی
    # =====================================================

    if state == "entry_fee":

        try:

            entry_fee = int(text)

            if entry_fee < 0:
                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ مبلغ باید عدد باشد."
            )

            return True

        context.user_data["current_entry_fee"] = entry_fee

        context.user_data["admin_state"] = "kill_prize"

        await update.message.reply_text(
            "🔫 جایزه هر کیل چقدر باشد؟\n\n"
            "مثال:\n"
            "25000"
        )

        return True

    # =====================================================
    # جایزه کیل
    # =====================================================

    if state == "kill_prize":

        try:

            kill_prize = int(text)

            if kill_prize < 0:
                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ مبلغ باید عدد باشد."
            )

            return True

        context.user_data["current_kill_prize"] = kill_prize

        context.user_data["admin_state"] = "first_prize"

        await update.message.reply_text(
            "🥇 جایزه تیم اول چقدر باشد؟"
        )

        return True

    # =====================================================
    # تیم اول
    # =====================================================

    if state == "first_prize":

        try:

            first_prize = int(text)

            if first_prize < 0:
                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ مبلغ باید عدد باشد."
            )

            return True

        context.user_data["current_first_prize"] = first_prize

        context.user_data["admin_state"] = "second_prize"

        await update.message.reply_text(
            "🥈 جایزه تیم دوم چقدر باشد؟"
        )

        return True

    # =====================================================
    # تیم دوم
    # =====================================================

    if state == "second_prize":

        try:

            second_prize = int(text)

            if second_prize < 0:
                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ مبلغ باید عدد باشد."
            )

            return True

        context.user_data["current_second_prize"] = second_prize

        context.user_data["admin_state"] = "third_prize"

        await update.message.reply_text(
            "🥉 جایزه تیم سوم چقدر باشد؟"
        )

        return True

    # =====================================================
    # تیم سوم
    # =====================================================

    if state == "third_prize":

        try:

            third_prize = int(text)

            if third_prize < 0:
                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ مبلغ باید عدد باشد."
            )

            return True

        context.user_data["current_third_prize"] = third_prize

        rooms = context.user_data["rooms"]

        rooms.append({
            "name": context.user_data["current_room_name"],
            "capacity": context.user_data["current_capacity"],
            "entry_fee": context.user_data["current_entry_fee"],
            "kill_prize": context.user_data["current_kill_prize"],
            "first_prize": context.user_data["current_first_prize"],
            "second_prize": context.user_data["current_second_prize"],
            "third_prize": third_prize,
        })

        current_room = context.user_data["current_room"]
        total_rooms = context.user_data["room_count"]

        if current_room < total_rooms:

            current_room += 1

            context.user_data["current_room"] = current_room

            context.user_data["admin_state"] = "room_name"

            await update.message.reply_text(
                f"🏠 روم {current_room} از {total_rooms}\n\n"
                "📝 اسم این روم را وارد کن:"
            )

            return True

        # =================================================
        # ساخت مسابقه و تمام روم‌ها
        # =================================================

        try:

            match_id = create_match(
                name=context.user_data["match_name"],
                match_date=context.user_data["match_date"],
                match_time=context.user_data["match_time"],
            )

            for room in rooms:

                create_room(
                    match_id=match_id,
                    name=room["name"],
                    capacity=room["capacity"],
                    entry_fee=room["entry_fee"],
                    kill_prize=room["kill_prize"],
                    first_prize=room["first_prize"],
                    second_prize=room["second_prize"],
                    third_prize=room["third_prize"],
                )

            context.user_data.clear()

            await update.message.reply_text(
                "✅ مسابقه با موفقیت ساخته شد!\n\n"
                f"🏆 مسابقه: {context.user_data.get('match_name', '') or 'ساخته شد'}\n"
                f"🆔 ID: {match_id}\n\n"
                f"🏠 تعداد روم: {total_rooms}\n\n"
                "هر روم تنظیمات مالی مستقل خودش را دارد.",
                reply_markup=admin_menu()
            )

        except Exception as error:

            print(
                "CREATE MATCH ERROR:",
                repr(error)
            )

            await update.message.reply_text(
                "❌ هنگام ساخت مسابقه خطایی رخ داد.\n\n"
                "Logs را بررسی کن."
            )

        return True

    return False
