import sqlite3
from contextlib import closing

DB_NAME = "1bd_bot.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def init_db():
    with closing(get_connection()) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            wallet INTEGER DEFAULT 0,
            bank_account TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            room_date TEXT NOT NULL,
            room_time TEXT NOT NULL,
            capacity INTEGER NOT NULL DEFAULT 64,
            entry_fee INTEGER NOT NULL DEFAULT 0,
            kill_prize INTEGER NOT NULL DEFAULT 0,
            first_prize INTEGER NOT NULL DEFAULT 0,
            second_prize INTEGER NOT NULL DEFAULT 0,
            third_prize INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            captain_id INTEGER NOT NULL,
            player1 TEXT NOT NULL,
            player2 TEXT NOT NULL,
            player3 TEXT NOT NULL,
            player4 TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
            FOREIGN KEY (captain_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(room_id, captain_id)
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            bank_account TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            receipt_type TEXT,
            receipt_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paid_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """)

        # برای دیتابیس‌های قبلی
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(users)").fetchall()
        }

        if "bank_account" not in columns:
            conn.execute(
                "ALTER TABLE users ADD COLUMN bank_account TEXT"
            )

        conn.commit()


# =========================================================
# USERS
# =========================================================

def create_user(telegram_id, username=None, first_name=None):
    with closing(get_connection()) as conn:
        conn.execute("""
            INSERT INTO users
            (telegram_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id)
            DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name
        """, (telegram_id, username, first_name))
        conn.commit()


def get_user(telegram_id):
    with closing(get_connection()) as conn:
        return conn.execute("""
            SELECT *
            FROM users
            WHERE telegram_id = ?
        """, (telegram_id,)).fetchone()


def get_user_by_id(user_id):
    with closing(get_connection()) as conn:
        return conn.execute("""
            SELECT *
            FROM users
            WHERE id = ?
        """, (user_id,)).fetchone()


# =========================================================
# WALLET
# =========================================================

def get_wallet(telegram_id):
    user = get_user(telegram_id)
    return user["wallet"] if user else 0


def add_wallet(telegram_id, amount, description=""):
    with closing(get_connection()) as conn:
        conn.execute("BEGIN IMMEDIATE")

        user = conn.execute("""
            SELECT id
            FROM users
            WHERE telegram_id = ?
        """, (telegram_id,)).fetchone()

        if not user:
            conn.rollback()
            return False

        conn.execute("""
            UPDATE users
            SET wallet = wallet + ?
            WHERE id = ?
        """, (amount, user["id"]))

        conn.execute("""
            INSERT INTO transactions
            (user_id, amount, type, description)
            VALUES (?, ?, ?, ?)
        """, (
            user["id"],
            amount,
            "wallet",
            description
        ))

        conn.commit()
        return True


def subtract_wallet(telegram_id, amount, description=""):
    with closing(get_connection()) as conn:
        conn.execute("BEGIN IMMEDIATE")

        user = conn.execute("""
            SELECT id, wallet
            FROM users
            WHERE telegram_id = ?
        """, (telegram_id,)).fetchone()

        if not user or user["wallet"] < amount:
            conn.rollback()
            return False

        conn.execute("""
            UPDATE users
            SET wallet = wallet - ?
            WHERE id = ?
        """, (amount, user["id"]))

        conn.execute("""
            INSERT INTO transactions
            (user_id, amount, type, description)
            VALUES (?, ?, ?, ?)
        """, (
            user["id"],
            -amount,
            "wallet_subtract",
            description
        ))

        conn.commit()
        return True


# =========================================================
# ROOMS
# =========================================================

def create_room(
    name,
    room_date,
    room_time,
    capacity,
    entry_fee,
    kill_prize,
    first_prize,
    second_prize,
    third_prize
):
    with closing(get_connection()) as conn:
        cursor = conn.execute("""
            INSERT INTO rooms
            (
                name,
                room_date,
                room_time,
                capacity,
                entry_fee,
                kill_prize,
                first_prize,
                second_prize,
                third_prize
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            room_date,
            room_time,
            capacity,
            entry_fee,
            kill_prize,
            first_prize,
            second_prize,
            third_prize
        ))

        conn.commit()
        return cursor.lastrowid


def get_rooms():
    with closing(get_connection()) as conn:
        return conn.execute("""
            SELECT *
            FROM rooms
            ORDER BY id DESC
        """).fetchall()


def get_open_rooms():
    with closing(get_connection()) as conn:
        return conn.execute("""
            SELECT *
            FROM rooms
            WHERE status = 'open'
            ORDER BY id ASC
        """).fetchall()


def get_room(room_id):
    with closing(get_connection()) as conn:
        return conn.execute("""
            SELECT *
            FROM rooms
            WHERE id = ?
        """, (room_id,)).fetchone()


def update_room(room_id, name=None, room_date=None, room_time=None):
    fields = []
    values = []

    if name is not None:
        fields.append("name = ?")
        values.append(name)

    if room_date is not None:
        fields.append("room_date = ?")
        values.append(room_date)

    if room_time is not None:
        fields.append("room_time = ?")
        values.append(room_time)

    if not fields:
        return False

    values.append(room_id)

    with closing(get_connection()) as conn:
        conn.execute(
            f"""
            UPDATE rooms
            SET {", ".join(fields)}
            WHERE id = ?
            """,
            values
        )
        conn.commit()

    return True


def get_room_team_count(room_id):
    with closing(get_connection()) as conn:
        row = conn.execute("""
            SELECT COUNT(*) AS count
            FROM teams
            WHERE room_id = ?
        """, (room_id,)).fetchone()

        return row["count"]


# =========================================================
# TEAM REGISTRATION
# =========================================================

def register_team(
    telegram_id,
    room_id,
    player1,
    player2,
    player3,
    player4
):
    """
    ثبت نهایی تیم + کسر ورودی + قفل ظرفیت
    در یک تراکنش اتمیک انجام می‌شود.
    """

    with closing(get_connection()) as conn:
        conn.execute("BEGIN IMMEDIATE")

        user = conn.execute("""
            SELECT id, wallet
            FROM users
            WHERE telegram_id = ?
        """, (telegram_id,)).fetchone()

        if not user:
            conn.rollback()
            return False, "user_not_found"

        room = conn.execute("""
            SELECT *
            FROM rooms
            WHERE id = ?
        """, (room_id,)).fetchone()

        if not room:
            conn.rollback()
            return False, "room_not_found"

        if room["status"] != "open":
            conn.rollback()
            return False, "room_closed"

        existing = conn.execute("""
            SELECT id
            FROM teams
            WHERE room_id = ?
            AND captain_id = ?
        """, (room_id, user["id"])).fetchone()

        if existing:
            conn.rollback()
            return False, "already_registered"

        count = conn.execute("""
            SELECT COUNT(*) AS count
            FROM teams
            WHERE room_id = ?
        """, (room_id,)).fetchone()["count"]

        if count >= room["capacity"]:
            conn.rollback()
            return False, "room_full"

        if user["wallet"] < room["entry_fee"]:
            conn.rollback()
            return False, "insufficient_wallet"

        cursor = conn.execute("""
            INSERT INTO teams
            (
                room_id,
                captain_id,
                player1,
                player2,
                player3,
                player4
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            room_id,
            user["id"],
            player1,
            player2,
            player3,
            player4
        ))

        if room["entry_fee"] > 0:
            conn.execute("""
                UPDATE users
                SET wallet = wallet - ?
                WHERE id = ?
            """, (room["entry_fee"], user["id"]))

            conn.execute("""
                INSERT INTO transactions
                (
                    user_id,
                    amount,
                    type,
                    description
                )
                VALUES (?, ?, ?, ?)
            """, (
                user["id"],
                -room["entry_fee"],
                "room_entry",
                f"Entry fee for room {room_id}"
            ))

        new_count = count + 1

        if new_count >= room["capacity"]:
            conn.execute("""
                UPDATE rooms
                SET status = 'full'
                WHERE id = ?
            """, (room_id,))

        conn.commit()

        return True, cursor.lastrowid


# =========================================================
# TEAM / PLAYER MANAGEMENT
# =========================================================

def get_captain_team(room_id, telegram_id):
    with closing(get_connection()) as conn:
        return conn.execute("""
            SELECT
                teams.*,
                users.telegram_id,
                users.username,
                users.first_name
            FROM teams
            JOIN users
                ON users.id = teams.captain_id
            WHERE teams.room_id = ?
            AND users.telegram_id = ?
        """, (room_id, telegram_id)).fetchone()


def get_team(team_id):
    with closing(get_connection()) as conn:
        return conn.execute("""
            SELECT
                teams.*,
                users.telegram_id AS captain_telegram_id,
                users.username AS captain_username,
                users.first_name AS captain_first_name,
                rooms.name AS room_name,
                rooms.room_date,
                rooms.room_time
            FROM teams
            JOIN users
                ON users.id = teams.captain_id
            JOIN rooms
                ON rooms.id = teams.room_id
            WHERE teams.id = ?
        """, (team_id,)).fetchone()


def get_room_teams(room_id):
    with closing(get_connection()) as conn:
        return conn.execute("""
            SELECT
                teams.*,
                users.telegram_id AS captain_telegram_id,
                users.username AS captain_username,
                users.first_name AS captain_first_name
            FROM teams
            JOIN users
                ON users.id = teams.captain_id
            WHERE teams.room_id = ?
            ORDER BY teams.id ASC
        """, (room_id,)).fetchall()


def update_team_player(team_id, player_number, new_value):
    if player_number not in (1, 2, 3, 4):
        return False

    column = f"player{player_number}"

    with closing(get_connection()) as conn:
        conn.execute(
            f"""
            UPDATE teams
            SET {column} = ?
            WHERE id = ?
            """,
            (new_value, team_id)
        )
        conn.commit()

    return True


# =========================================================
# CANCEL TEAM / REFUND
# =========================================================

def cancel_team(team_id, telegram_id):
    with closing(get_connection()) as conn:
        conn.execute("BEGIN IMMEDIATE")

        row = conn.execute("""
            SELECT
                teams.id,
                teams.room_id,
                users.id AS user_id,
                users.telegram_id,
                rooms.entry_fee,
                rooms.status
            FROM teams
            JOIN users
                ON users.id = teams.captain_id
            JOIN rooms
                ON rooms.id = teams.room_id
            WHERE teams.id = ?
            AND users.telegram_id = ?
        """, (team_id, telegram_id)).fetchone()

        if not row:
            conn.rollback()
            return False, "not_found"

        conn.execute("""
            DELETE FROM teams
            WHERE id = ?
        """, (team_id,))

        if row["entry_fee"] > 0:
            conn.execute("""
                UPDATE users
                SET wallet = wallet + ?
                WHERE id = ?
            """, (row["entry_fee"], row["user_id"]))

            conn.execute("""
                INSERT INTO transactions
                (
                    user_id,
                    amount,
                    type,
                    description
                )
                VALUES (?, ?, ?, ?)
            """, (
                row["user_id"],
                row["entry_fee"],
                "room_cancel_refund",
                f"Refund for room {row['room_id']}"
            ))

        if row["status"] == "full":
            conn.execute("""
                UPDATE rooms
                SET status = 'open'
                WHERE id = ?
            """, (row["room_id"],))

        conn.commit()
        return True, row["entry_fee"]


# =========================================================
# DELETE ROOM + REFUND ALL
# =========================================================

def delete_room_and_refund(room_id):
    with closing(get_connection()) as conn:
        conn.execute("BEGIN IMMEDIATE")

        room = conn.execute("""
            SELECT *
            FROM rooms
            WHERE id = ?
        """, (room_id,)).fetchone()

        if not room:
            conn.rollback()
            return []

        teams = conn.execute("""
            SELECT
                teams.id,
                users.id AS user_id,
                users.telegram_id
            FROM teams
            JOIN users
                ON users.id = teams.captain_id
            WHERE teams.room_id = ?
        """, (room_id,)).fetchall()

        captains = []

        for team in teams:
            if room["entry_fee"] > 0:
                conn.execute("""
                    UPDATE users
                    SET wallet = wallet + ?
                    WHERE id = ?
                """, (
                    room["entry_fee"],
                    team["user_id"]
                ))

                conn.execute("""
                    INSERT INTO transactions
                    (
                        user_id,
                        amount,
                        type,
                        description
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    team["user_id"],
                    room["entry_fee"],
                    "room_deleted_refund",
                    f"Refund for deleted room {room_id}"
                ))

            captains.append(team["telegram_id"])

        conn.execute("""
            DELETE FROM teams
            WHERE room_id = ?
        """, (room_id,))

        conn.execute("""
            DELETE FROM rooms
            WHERE id = ?
        """, (room_id,))

        conn.commit()
        return captains


# =========================================================
# USER ROOMS
# =========================================================

def get_user_rooms(telegram_id):
    with closing(get_connection()) as conn:
        return conn.execute("""
            SELECT
                rooms.*,
                teams.id AS team_id,
                teams.player1,
                teams.player2,
                teams.player3,
                teams.player4
            FROM teams
            JOIN rooms
                ON rooms.id = teams.room_id
            JOIN users
                ON users.id = teams.captain_id
            WHERE users.telegram_id = ?
            ORDER BY rooms.id DESC
        """, (telegram_id,)).fetchall()


# =========================================================
# BANK
# =========================================================

def get_bank_account(telegram_id):
    user = get_user(telegram_id)
    return user["bank_account"] if user else None


def set_bank_account(telegram_id, bank_account):
    with closing(get_connection()) as conn:
        conn.execute("""
            UPDATE users
            SET bank_account = ?
            WHERE telegram_id = ?
        """, (bank_account, telegram_id))
        conn.commit()
        return True


# =========================================================
# WITHDRAWALS
# =========================================================

def create_withdrawal(telegram_id, amount):
    with closing(get_connection()) as conn:
        conn.execute("BEGIN IMMEDIATE")

        user = conn.execute("""
            SELECT id, wallet, bank_account
            FROM users
            WHERE telegram_id = ?
        """, (telegram_id,)).fetchone()

        if not user:
            conn.rollback()
            return False, "user_not_found"

        if not user["bank_account"]:
            conn.rollback()
            return False, "no_bank"

        if amount <= 0:
            conn.rollback()
            return False, "invalid_amount"

        if user["wallet"] < amount:
            conn.rollback()
            return False, "insufficient_wallet"

        pending = conn.execute("""
            SELECT id
            FROM withdrawals
            WHERE user_id = ?
            AND status = 'pending'
        """, (user["id"],)).fetchone()

        if pending:
            conn.rollback()
            return False, "pending_exists"

        cursor = conn.execute("""
            INSERT INTO withdrawals
            (
                user_id,
                amount,
                bank_account
            )
            VALUES (?, ?, ?)
        """, (
            user["id"],
            amount,
            user["bank_account"]
        ))

        conn.commit()
        return True, cursor.lastrowid


def get_withdrawals(status=None):
    with closing(get_connection()) as conn:
        if status:
            return conn.execute("""
                SELECT
                    withdrawals.*,
                    users.telegram_id,
                    users.username,
                    users.first_name,
                    users.wallet
                FROM withdrawals
                JOIN users
                    ON users.id = withdrawals.user_id
                WHERE withdrawals.status = ?
                ORDER BY withdrawals.id DESC
            """, (status,)).fetchall()

        return conn.execute("""
            SELECT
                withdrawals.*,
                users.telegram_id,
                users.username,
                users.first_name,
                users.wallet
            FROM withdrawals
            JOIN users
                ON users.id = withdrawals.user_id
            ORDER BY withdrawals.id DESC
        """).fetchall()


def get_withdrawal(withdrawal_id):
    with closing(get_connection()) as conn:
        return conn.execute("""
            SELECT
                withdrawals.*,
                users.telegram_id,
                users.username,
                users.first_name,
                users.wallet
            FROM withdrawals
            JOIN users
                ON users.id = withdrawals.user_id
            WHERE withdrawals.id = ?
        """, (withdrawal_id,)).fetchone()


def complete_withdrawal(
    withdrawal_id,
    receipt_type,
    receipt_data
):
    """
    مبلغ دقیق درخواست‌شده در همین تراکنش از کیف پول کم می‌شود.
    """

    with closing(get_connection()) as conn:
        conn.execute("BEGIN IMMEDIATE")

        withdrawal = conn.execute("""
            SELECT
                withdrawals.*,
                users.wallet,
                users.id AS user_id,
                users.telegram_id
            FROM withdrawals
            JOIN users
                ON users.id = withdrawals.user_id
            WHERE withdrawals.id = ?
        """, (withdrawal_id,)).fetchone()

        if not withdrawal:
            conn.rollback()
            return False, "not_found"

        if withdrawal["status"] != "pending":
            conn.rollback()
            return False, "already_processed"

        if withdrawal["wallet"] < withdrawal["amount"]:
            conn.rollback()
            return False, "insufficient_wallet"

        conn.execute("""
            UPDATE users
            SET wallet = wallet - ?
            WHERE id = ?
        """, (
            withdrawal["amount"],
            withdrawal["user_id"]
        ))

        conn.execute("""
            INSERT INTO transactions
            (
                user_id,
                amount,
                type,
                description
            )
            VALUES (?, ?, ?, ?)
        """, (
            withdrawal["user_id"],
            -withdrawal["amount"],
            "withdrawal",
            f"Withdrawal #{withdrawal_id}"
        ))

        conn.execute("""
            UPDATE withdrawals
            SET
                status = 'paid',
                receipt_type = ?,
                receipt_data = ?,
                paid_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            receipt_type,
            receipt_data,
            withdrawal_id
        ))

        conn.commit()

        return True, withdrawal["telegram_id"]


# =========================================================
# ADMIN USER SEARCH
# =========================================================

def find_user_by_telegram_id(telegram_id):
    return get_user(telegram_id)


# =========================================================
# INIT
# =========================================================

init_db()
