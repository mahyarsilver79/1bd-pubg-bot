import sqlite3
from contextlib import closing

DB_NAME = "1bd_bot.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# =========================================================
# DATABASE
# =========================================================

def init_db():

    with closing(get_connection()) as conn:

        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            wallet INTEGER DEFAULT 0,
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

            FOREIGN KEY (room_id)
                REFERENCES rooms(id)
                ON DELETE CASCADE,

            FOREIGN KEY (captain_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            amount INTEGER NOT NULL,

            type TEXT NOT NULL,

            description TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );
        """)

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

        conn.execute("""
            INSERT OR IGNORE INTO users
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


# =========================================================
# WALLET
# =========================================================

def get_wallet(telegram_id):

    user = get_user(telegram_id)

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


# =========================================================
# CREATE ROOM
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


# =========================================================
# ROOMS
# =========================================================

def get_rooms():

    with closing(get_connection()) as conn:

        return conn.execute("""
            SELECT *
            FROM rooms
            ORDER BY room_date ASC,
                     room_time ASC,
                     id ASC
        """).fetchall()


def get_open_rooms():

    with closing(get_connection()) as conn:

        return conn.execute("""
            SELECT *
            FROM rooms
            WHERE status = 'open'
            ORDER BY room_date ASC,
                     room_time ASC,
                     id ASC
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


# =========================================================
# UPDATE ROOM
# =========================================================

def update_room(
    room_id,
    name=None,
    room_date=None,
    room_time=None,
    capacity=None,
    entry_fee=None,
    kill_prize=None,
    first_prize=None,
    second_prize=None,
    third_prize=None
):

    fields = []
    values = []

    data = [
        ("name", name),
        ("room_date", room_date),
        ("room_time", room_time),
        ("capacity", capacity),
        ("entry_fee", entry_fee),
        ("kill_prize", kill_prize),
        ("first_prize", first_prize),
        ("second_prize", second_prize),
        ("third_prize", third_prize)
    ]

    for field, value in data:

        if value is not None:

            fields.append(f"{field} = ?")
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
# ROOM TEAMS
# =========================================================

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
        """, (
            room_id,
        )).fetchall()


# =========================================================
# TEAM COUNT
# =========================================================

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


# =========================================================
# DELETE ROOM + REFUND CAPTAINS
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
                users.telegram_id
            FROM teams

            JOIN users
                ON users.id = teams.captain_id

            WHERE teams.room_id = ?
        """, (
            room_id,
        )).fetchall()

        refunded_captains = []

        for team in teams:

            captain_id = conn.execute("""
                SELECT captain_id
                FROM teams
                WHERE id = ?
            """, (
                team["id"],
            )).fetchone()["captain_id"]

            conn.execute("""
                UPDATE users
                SET wallet = wallet + ?
                WHERE id = ?
            """, (
                room["entry_fee"],
                captain_id
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
                captain_id,
                room["entry_fee"],
                "room_deleted_refund",
                f"Refund for deleted room {room_id}"
            ))

            refunded_captains.append(
                team["telegram_id"]
            )

        conn.execute("""
            DELETE FROM rooms
            WHERE id = ?
        """, (
            room_id,
        ))

        conn.commit()

        return refunded_captains


# =========================================================
# INITIALIZE
# =========================================================

init_db()
