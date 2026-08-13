if state == "room_name":

    context.user_data["current_room_name"] = text

    context.user_data["admin_state"] = "room_capacity"

    await update.message.reply_text(
        "📝 اسم روم را وارد کن:",
        reply_markup=cancel_menu()
    )

    return True


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
        "👥 ظرفیت روم را وارد کن:",
        reply_markup=cancel_menu()
    )

    return True


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
        "💰 ورودی روم را وارد کن:",
        reply_markup=cancel_menu()
    )

    return True


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
        "🔫 جایزه هر کیل را وارد کن:",
        reply_markup=cancel_menu()
    )

    return True


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
        "🥇 جایزه نفر اول را وارد کن:",
        reply_markup=cancel_menu()
    )

    return True


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
        "🥈 جایزه نفر دوم را وارد کن:",
        reply_markup=cancel_menu()
    )

    return True


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

    await update.message.reply_text(
        "🥉 جایزه نفر سوم را وارد کن:",
        reply_markup=cancel_menu()
    )

    return True
