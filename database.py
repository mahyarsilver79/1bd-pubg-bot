import sqlite3
from contextlib import closing


DB_NAME = "1bd_bot.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# =========================================================
# DATABASE INIT
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


        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            match_date TEXT,
            match_time TEXT,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );


        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            match_id INTEGER NOT NULL,

            name TEXT NOT NULL,

            capacity INTEGER DEFAULT 64,

            entry_fee INTEGER DEFAULT 0,

            kill_prize INTEGER DEFAULT 0,

            first_prize INTEGER DEFAULT 0,

            second_prize INTEGER DEFAULT 0,

            third_prize INTEGER DEFAULT 0,

            status TEXT DEFAULT 'open',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (match_id)
                REFERENCES matches(id)
                ON DELETE CASCADE
        );


        CREATE TABLE IF NOT EXISTS squads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            room_id INTEGER NOT NULL,

            squad_number INTEGER NOT NULL,

            FOREIGN KEY (room_id)
                REFERENCES rooms(id)
                ON DELETE CASCADE
        );


        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            room_id INTEGER NOT NULL,

            squad_id INTEGER,

            status TEXT DEFAULT 'active',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (room_id)
                REFERENCES rooms(id)
                ON DELETE CASCADE,

            FOREIGN KEY (squad_id)
                REFERENCES squads(id)
                ON DELETE SET NULL
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

        # اضافه کردن ستون‌های جدید به دیتابیس‌های قدیمی
        columns = conn.execute("""
            PRAGMA table_info(matches)
        """).fetchall()

        column_names = [column["name"] for column in columns]

        if "match_date" not in column_names:

            conn.execute("""
                ALTER TABLE matches
                ADD COLUMN match_date TEXT
            """)

        if "match_time" not in column_names:

            conn.execute("""
                ALTER TABLE matches
                ADD COLUMN match_time TEXT
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

        conn.execute("""
            UPDATE users

            SET wallet = wallet + ?

            WHERE telegram_id = ?
        """, (
            amount,
            telegram_id
        ))

        user = conn.execute("""
            SELECT id
            FROM users
            WHERE telegram_id = ?
        """, (
            telegram_id,
        )).fetchone()

        if user:

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


# =========================================================
# MATCHES
# =========================================================

def create_match(
    name,
    match_date=None,
    match_time=None
):

    with closing(get_connection()) as conn:

        cursor = conn.execute("""
            INSERT INTO matches
            (
                name,
                match_date,
                match_time
            )
            VALUES (?, ?, ?)
        """, (
            name,
            match_date,
            match_time
        ))

        conn.commit()

        return cursor.lastrowid


def get_match(match_id):

    with closing(get_connection()) as conn:

        return conn.execute("""
            SELECT *
            FROM matches
            WHERE id = ?
        """, (
            match_id,
        )).fetchone()


def get_matches():

    with closing(get_connection()) as conn:

        return conn.execute("""
            SELECT *
            FROM matches
            ORDER BY id DESC
        """).fetchall()


def get_open_matches():

    with closing(get_connection()) as conn:

        return conn.execute("""
            SELECT *
            FROM matches
            WHERE status = 'open'
            ORDER BY id ASC
        """).fetchall()


def close_match(match_id):

    with closing(get_connection()) as conn:

        conn.execute("""
            UPDATE matches
            SET status = 'closed'
            WHERE id = ?
        """, (
            match_id,
        ))

        conn.commit()


# =========================================================
# ROOMS
# =========================================================

def create_room(
    match_id,
    name,
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
                match_id,
                name,
                capacity,
                entry_fee,
                kill_prize,
                first_prize,
                second_prize,
                third_prize
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match_id,
            name,
            capacity,
            entry_fee,
            kill_prize,
            first_prize,
            second_prize,
            third_prize
        ))

        conn.commit()

        return cursor.lastrowid


def get_room(room_id):

    with closing(get_connection()) as conn:

        return conn.execute("""
            SELECT *
            FROM rooms
            WHERE id = ?
        """, (
            room_id,
        )).fetchone()


def get_open_rooms(match_id):

    with closing(get_connection()) as conn:

        return conn.execute("""
            SELECT *
            FROM rooms
            WHERE match_id = ?

            AND status = 'open'

            ORDER BY id ASC
        """, (
            match_id,
        )).fetchall()


def get_match_rooms(match_id):

    with closing(get_connection()) as conn:

        return conn.execute("""
            SELECT *
            FROM rooms
            WHERE match_id = ?

            ORDER BY id ASC
        """, (
            match_id,
        )).fetchall()


# =========================================================
# ROOM STATISTICS
# =========================================================

def get_room_player_count(room_id):

    with closing(get_connection()) as conn:

        result = conn.execute("""
            SELECT COUNT(*) AS count

            FROM registrations

            WHERE room_id = ?

            AND status = 'active'
        """, (
            room_id,
        )).fetchone()

        return result["count"]


def get_room_revenue(room_id):

    room = get_room(room_id)

    if not room:
        return 0

    players = get_room_player_count(room_id)

    return players * room["entry_fee"]


def get_room_total_prizes(room_id):

    room = get_room(room_id)

    if not room:
        return 0

    players = get_room_player_count(room_id)

    kill_prizes = players * room["kill_prize"]

    team_prizes = (
        room["first_prize"]
        + room["second_prize"]
        + room["third_prize"]
    )

    return kill_prizes + team_prizes


def get_room_profit(room_id):

    revenue = get_room_revenue(room_id)

    prizes = get_room_total_prizes(room_id)

    return revenue - prizes


# =========================================================
# MATCH FINANCIAL STATISTICS
# =========================================================

def get_match_financials(match_id):

    rooms = get_match_rooms(match_id)

    total_revenue = 0
    total_prizes = 0

    for room in rooms:

        players = get_room_player_count(
            room["id"]
        )

        revenue = (
            players
            * room["entry_fee"]
        )

        kill_prizes = (
            players
            * room["kill_prize"]
        )

        team_prizes = (
            room["first_prize"]
            + room["second_prize"]
            + room["third_prize"]
        )

        total_revenue += revenue

        total_prizes += (
            kill_prizes
            + team_prizes
        )

    return {
        "revenue": total_revenue,
        "prizes": total_prizes,
        "profit": total_revenue - total_prizes,
    }


# =========================================================
# FIND AVAILABLE ROOM
# =========================================================

def find_available_room(match_id):

    rooms = get_open_rooms(match_id)

    for room in rooms:

        players = get_room_player_count(
            room["id"]
        )

        if players < room["capacity"]:

            return room

    return None


# =========================================================
# SQUADS
# =========================================================

def create_squad(room_id):

    with closing(get_connection()) as conn:

        result = conn.execute("""
            SELECT MAX(squad_number) AS max_number

            FROM squads

            WHERE room_id = ?
        """, (
            room_id,
        )).fetchone()

        next_number = (
            result["max_number"] or 0
        ) + 1

        cursor = conn.execute("""
            INSERT INTO squads
            (
                room_id,
                squad_number
            )
            VALUES (?, ?)
        """, (
            room_id,
            next_number
        ))

        conn.commit()

        return cursor.lastrowid


def get_available_squad(room_id):

    with closing(get_connection()) as conn:

        squads = conn.execute("""
            SELECT *
            FROM squads

            WHERE room_id = ?

            ORDER BY squad_number ASC
        """, (
            room_id,
        )).fetchall()

        for squad in squads:

            count = conn.execute("""
                SELECT COUNT(*) AS count

                FROM registrations

                WHERE squad_id = ?

                AND status = 'active'
            """, (
                squad["id"],
            )).fetchone()["count"]

            if count < 4:

                return squad

    return None


# =========================================================
# REGISTRATION
# =========================================================

def register_player(
    telegram_id,
    room_id
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

            return False, "user_not_found"

        existing = conn.execute("""
            SELECT id

            FROM registrations

            WHERE user_id = ?

            AND room_id = ?

            AND status = 'active'
        """, (
            user["id"],
            room_id
        )).fetchone()

        if existing:

            return False, "already_registered"

        room = conn.execute("""
            SELECT *

            FROM rooms

            WHERE id = ?
        """, (
            room_id,
        )).fetchone()

        if not room:

            return False, "room_not_found"

        count = conn.execute("""
            SELECT COUNT(*) AS count

            FROM registrations

            WHERE room_id = ?

            AND status = 'active'
        """, (
            room_id,
        )).fetchone()["count"]

        if count >= room["capacity"]:

            return False, "room_full"

        squad = get_available_squad(room_id)

        if not squad:

            result = conn.execute("""
                SELECT MAX(squad_number) AS max_number

                FROM squads

                WHERE room_id = ?
            """, (
                room_id,
            )).fetchone()

            max_number = (
                result["max_number"] or 0
            )

            conn.execute("""
                INSERT INTO squads
                (
                    room_id,
                    squad_number
                )
                VALUES (?, ?)
            """, (
                room_id,
                max_number + 1
            ))

            squad = conn.execute("""
                SELECT *

                FROM squads

                WHERE room_id = ?

                AND squad_number = ?
            """, (
                room_id,
                max_number + 1
            )).fetchone()

        conn.execute("""
            INSERT INTO registrations
            (
                user_id,
                room_id,
                squad_id
            )
            VALUES (?, ?, ?)
        """, (
            user["id"],
            room_id,
            squad["id"]
        ))

        conn.commit()

        return True, squad["squad_number"]


# =========================================================
# CANCEL REGISTRATION
# =========================================================

def cancel_registration(
    telegram_id,
    room_id
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

        registration = conn.execute("""
            SELECT id

            FROM registrations

            WHERE user_id = ?

            AND room_id = ?

            AND status = 'active'
        """, (
            user["id"],
            room_id
        )).fetchone()

        if not registration:
            return False

        room = conn.execute("""
            SELECT entry_fee

            FROM rooms

            WHERE id = ?
        """, (
            room_id,
        )).fetchone()

        conn.execute("""
            UPDATE registrations

            SET status = 'cancelled'

            WHERE id = ?
        """, (
            registration["id"],
        ))

        conn.execute("""
            UPDATE users

            SET wallet = wallet + ?

            WHERE id = ?
        """, (
            room["entry_fee"],
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
            room["entry_fee"],
            "cancel_refund",
            "Refund after cancellation"
        ))

        conn.commit()

        return True


# =========================================================
# USER MATCHES
# =========================================================

def get_user_matches(telegram_id):

    with closing(get_connection()) as conn:

        return conn.execute("""
            SELECT

                matches.name AS match_name,

                matches.match_date,

                matches.match_time,

                rooms.name AS room_name,

                rooms.id AS room_id,

                squads.squad_number

            FROM registrations

            JOIN users
                ON users.id = registrations.user_id

            JOIN rooms
                ON rooms.id = registrations.room_id

            JOIN matches
                ON matches.id = rooms.match_id

            LEFT JOIN squads
                ON squads.id = registrations.squad_id

            WHERE users.telegram_id = ?

            AND registrations.status = 'active'

            ORDER BY registrations.id DESC

        """, (
            telegram_id,
        )).fetchall()


# =========================================================
# INITIALIZE
# =========================================================

init_db()
