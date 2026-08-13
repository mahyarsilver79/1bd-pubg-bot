import sqlite3
from contextlib import closing

DB_NAME = "1bd_bot.db"


def get_connection():

    conn = sqlite3.connect(DB_NAME)

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


def init_db():

    with closing(get_connection()) as conn:

        conn.executescript("""

        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            telegram_id INTEGER UNIQUE NOT NULL,

            username TEXT,

            first_name TEXT,

            last_name TEXT,

            phone TEXT,

            wallet INTEGER DEFAULT 0,

            created_at
            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

            created_at
            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );


        CREATE TABLE IF NOT EXISTS teams (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            room_id INTEGER NOT NULL,

            captain_id INTEGER NOT NULL,

            player1 TEXT NOT NULL,

            player2 TEXT NOT NULL,

            player3 TEXT NOT NULL,

            player4 TEXT NOT NULL,

            created_at
            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(room_id)
            REFERENCES rooms(id)
            ON DELETE CASCADE,

            FOREIGN KEY(captain_id)
            REFERENCES users(id)
            ON DELETE CASCADE
        );


        CREATE TABLE IF NOT EXISTS transactions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            amount INTEGER NOT NULL,

            type TEXT NOT NULL,

            description TEXT,

            created_at
            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
            REFERENCES users(id)
            ON DELETE CASCADE
        );


        CREATE TABLE IF NOT EXISTS registrations (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            room_id INTEGER NOT NULL,

            created_at
            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
            REFERENCES users(id)
            ON DELETE CASCADE,

            FOREIGN KEY(room_id)
            REFERENCES rooms(id)
            ON DELETE CASCADE
        );

        """)

        # مهاجرت دیتابیس قدیمی
        columns = conn.execute(
            "PRAGMA table_info(users)"
        ).fetchall()

        column_names = {
            row["name"]
            for row in columns
        }

        if "last_name" not in column_names:

            conn.execute(
                "ALTER TABLE users ADD COLUMN last_name TEXT"
            )

        if "phone" not in column_names:

            conn.execute(
                "ALTER TABLE users ADD COLUMN phone TEXT"
            )

        conn.commit()


# =========================================================
# USERS
# =========================================================

def create_user(
    telegram_id,
    username=None,
    first_name=None
):

    with closing(get_connection()) as conn:

        existing = conn.execute("""
            SELECT id
            FROM users
            WHERE telegram_id = ?
        """, (
            telegram_id,
        )).fetchone()

        if existing:

            conn.execute("""
                UPDATE users

                SET username = ?,
                    first_name = ?

                WHERE telegram_id = ?
            """, (
                username,
                first_name,
                telegram_id
            ))

        else:

            conn.execute("""
                INSERT INTO users
                (
                    telegram_id,
                    username,
                    first_name
                )
                VALUES (?, ?, ?)
            """, (
                telegram_id,
                username,
                first_name
            ))

        conn.commit()


def get_user(telegram_id):

    with closing(get_connection()) as conn:

        return conn.execute("""
            SELECT *
            FROM users
            WHERE telegram_id = ?
        """, (
            telegram_id,
        )).fetchone()


def complete_user_registration(
    telegram_id,
    first_name,
    last_name,
    phone
):

    with closing(get_connection()) as conn:

        conn.execute("""
            UPDATE users

            SET first_name = ?,
                last_name = ?,
                phone = ?

            WHERE telegram_id = ?
        """, (
            first_name,
            last_name,
            phone,
            telegram_id
        ))

        conn.commit()


# =========================================================
# USER SEARCH
# =========================================================

def find_user(search):

    search = search.strip()

    if search.startswith("@"):

        search = search[1:]

    with closing(get_connection()) as conn:

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE username = ?
               OR CAST(telegram_id AS TEXT) = ?
        """, (
            search,
            search
        )).fetchone()

        return user


# =========================================================
# WALLET
# =========================================================

def get_wallet(telegram_id):

    user = get_user(
        telegram_id
    )

    if not user:
        return 0

    return user["wallet"]


def add_wallet(
    telegram_id,
    amount,
    description=""
):

    with closing(get_connection()) as conn:

        user = conn.execute("""
            SELECT id
            FROM users
            WHERE telegram_id = ?
        """, (
            telegram_id,
        )).fetchone()

        if not user:
            return False

        conn.execute("""
            UPDATE users

            SET wallet = wallet + ?

            WHERE id = ?
        """, (
            amount,
            user["id"]
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
            user["id"],
            amount,
            "wallet",
            description
        ))

        conn.commit()

        return True


def admin_change_wallet(
    telegram_id,
    amount,
    description
):

    with closing(get_connection()) as conn:

        user = conn.execute("""
            SELECT id, wallet
            FROM users
            WHERE telegram_id = ?
        """, (
            telegram_id,
        )).fetchone()

        if not user:
            return False, "user_not_found"

        new_balance = (
            user["wallet"] + amount
        )

        if new_balance < 0:
            return False, "insufficient_balance"

        conn.execute("""
            UPDATE users

            SET wallet = ?

            WHERE id = ?
        """, (
            new_balance,
            user["id"]
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
            user["id"],
            amount,
            "admin_wallet",
            description
        ))

        conn.commit()

        return True, new_balance


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

            ORDER BY id DESC
        """).fetchall()


def get_room(room_id):

    with closing(get_connection()) as conn:

        return conn.execute("""
            SELECT *
            FROM rooms

            WHERE id = ?
        """, (
            room_id,
        )).fetchone()


def update_room(
    room_id,
    name=None,
    room_date=None,
    room_time=None
):

    fields = []
    values = []

    data = [
        ("name", name),
        ("room_date", room_date),
        ("room_time", room_time)
    ]

    for field, value in data:

        if value is not None:

            fields.append(
                f"{field} = ?"
            )

            values.append(value)

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


# =========================================================
# TEAMS
# =========================================================

def create_team(
    room_id,
    captain_telegram_id,
    player1,
    player2,
    player3,
    player4
):

    with closing(get_connection()) as conn:

        user = conn.execute("""
            SELECT id
            FROM users

            WHERE telegram_id = ?
        """, (
            captain_telegram_id,
        )).fetchone()

        if not user:
            return None

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

        conn.commit()

        return cursor.lastrowid


def get_room_teams(room_id):

    with closing(get_connection()) as conn:

        return conn.execute("""
            SELECT
                teams.*,

                users.telegram_id
                AS captain_telegram_id,

                users.username
                AS captain_username,

                users.first_name
                AS captain_first_name,

                users.last_name
                AS captain_last_name

            FROM teams

            JOIN users
            ON users.id = teams.captain_id

            WHERE teams.room_id = ?

            ORDER BY teams.id ASC
        """, (
            room_id,
        )).fetchall()


def get_room_team_count(room_id):

    with closing(get_connection()) as conn:

        result = conn.execute("""
            SELECT COUNT(*) AS count

            FROM teams

            WHERE room_id = ?
        """, (
            room_id,
        )).fetchone()

        return result["count"]


def get_captain_team(
    room_id,
    captain_telegram_id
):

    with closing(get_connection()) as conn:

        return conn.execute("""
            SELECT teams.*

            FROM teams

            JOIN users
            ON users.id = teams.captain_id

            WHERE teams.room_id = ?

            AND users.telegram_id = ?
        """, (
            room_id,
            captain_telegram_id
        )).fetchone()


def update_team_players(
    team_id,
    player1,
    player2,
    player3,
    player4
):

    with closing(get_connection()) as conn:

        conn.execute("""
            UPDATE teams

            SET
                player1 = ?,
                player2 = ?,
                player3 = ?,
                player4 = ?

            WHERE id = ?
        """, (
            player1,
            player2,
            player3,
            player4,
            team_id
        ))

        conn.commit()

        return True


# =========================================================
# DELETE ROOM + REFUND
# =========================================================

def delete_room_and_refund(room_id):

    with closing(get_connection()) as conn:

        room = conn.execute("""
            SELECT *
            FROM rooms

            WHERE id = ?
        """, (
            room_id,
        )).fetchone()

        if not room:
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
        """, (
            room_id,
        )).fetchall()

        refunded = []

        for team in teams:

            conn.execute("""
                UPDATE users

                SET wallet =
                    wallet + ?

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

            refunded.append(
                team["telegram_id"]
            )

        conn.execute("""
            DELETE FROM registrations
            WHERE room_id = ?
        """, (
            room_id,
        ))

        conn.execute("""
            DELETE FROM teams
            WHERE room_id = ?
        """, (
            room_id,
        ))

        conn.execute("""
            DELETE FROM rooms
            WHERE id = ?
        """, (
            room_id,
        ))

        conn.commit()

        return refunded


# =========================================================
# USER ROOMS
# =========================================================

def get_user_rooms(telegram_id):

    with closing(get_connection()) as conn:

        return conn.execute("""
            SELECT DISTINCT rooms.*

            FROM rooms

            JOIN teams
            ON teams.room_id = rooms.id

            JOIN users
            ON users.id = teams.captain_id

            WHERE users.telegram_id = ?

            ORDER BY rooms.id DESC
        """, (
            telegram_id,
        )).fetchall()


# =========================================================
# OLD COMPATIBILITY
# =========================================================

def register_player(
    user_id,
    room_id
):

    return False


def get_user_matches(
    telegram_id
):

    return get_user_rooms(
        telegram_id
    )


# =========================================================
# INIT
# =========================================================

init_db()
