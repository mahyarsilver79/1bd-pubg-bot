import sqlite3
from contextlib import closing

DB_NAME = "1bd_bot.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            start_time TEXT,
            capacity INTEGER DEFAULT 64,
            entry_fee INTEGER DEFAULT 50000,
            kill_prize INTEGER DEFAULT 25000,
            first_prize INTEGER DEFAULT 300000,
            second_prize INTEGER DEFAULT 200000,
            third_prize INTEGER DEFAULT 100000,
            status TEXT DEFAULT 'open',
            FOREIGN KEY (match_id) REFERENCES matches(id)
        );

        CREATE TABLE IF NOT EXISTS squads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            squad_number INTEGER NOT NULL,
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        );

        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            squad_id INTEGER,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (room_id) REFERENCES rooms(id),
            FOREIGN KEY (squad_id) REFERENCES squads(id)
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """)

        conn.commit()


def create_user(telegram_id, username=None, first_name=None):
    with closing(get_connection()) as conn:
        conn.execute("""
            INSERT OR IGNORE INTO users
            (telegram_id, username, first_name)
            VALUES (?, ?, ?)
        """, (telegram_id, username, first_name))

        conn.commit()


def get_user(telegram_id):
    with closing(get_connection()) as conn:
        return conn.execute("""
            SELECT * FROM users
            WHERE telegram_id = ?
        """, (telegram_id,)).fetchone()


def get_wallet(telegram_id):
    user = get_user(telegram_id)

    if not user:
        return 0

    return user["wallet"]


def add_wallet(telegram_id, amount, description=""):
    with closing(get_connection()) as conn:
        conn.execute("""
            UPDATE users
            SET wallet = wallet + ?
            WHERE telegram_id = ?
        """, (amount, telegram_id))

        user = conn.execute("""
            SELECT id FROM users
            WHERE telegram_id = ?
        """, (telegram_id,)).fetchone()

        if user:
            conn.execute("""
                INSERT INTO transactions
                (user_id, amount, type, description)
                VALUES (?, ?, ?, ?)
            """, (
                user["id"],
                amount,
                "wallet_credit",
                description
            ))

        conn.commit()


def create_match(name):
    with closing(get_connection()) as conn:
        cursor = conn.execute("""
            INSERT INTO matches (name)
            VALUES (?)
        """, (name,))

        conn.commit()
        return cursor.lastrowid


def create_room(
    match_id,
    name,
    start_time,
    capacity=64,
    entry_fee=50000,
    kill_prize=25000,
    first_prize=300000,
    second_prize=200000,
    third_prize=100000
):
    with closing(get_connection()) as conn:
        cursor = conn.execute("""
            INSERT INTO rooms (
                match_id,
                name,
                start_time,
                capacity,
                entry_fee,
                kill_prize,
                first_prize,
                second_prize,
                third_prize
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match_id,
            name,
            start_time,
            capacity,
            entry_fee,
            kill_prize,
            first_prize,
            second_prize,
            third_prize
        ))

        conn.commit()
        return cursor.lastrowid


def get_open_rooms(match_id):
    with closing(get_connection()) as conn:
        return conn.execute("""
            SELECT *
            FROM rooms
            WHERE match_id = ?
            AND status = 'open'
            ORDER BY id ASC
        """, (match_id,)).fetchall()


def get_room_player_count(room_id):
    with closing(get_connection()) as conn:
        result = conn.execute("""
            SELECT COUNT(*) AS count
            FROM registrations
            WHERE room_id = ?
            AND status = 'active'
        """, (room_id,)).fetchone()

        return result["count"]


def find_available_room(match_id):
    rooms = get_open_rooms(match_id)

    for room in rooms:
        count = get_room_player_count(room["id"])

        if count < room["capacity"]:
            return room

    return None


def create_squad(room_id):
    with closing(get_connection()) as conn:
        result = conn.execute("""
            SELECT MAX(squad_number) AS max_number
            FROM squads
            WHERE room_id = ?
        """, (room_id,)).fetchone()

        next_number = (result["max_number"] or 0) + 1

        cursor = conn.execute("""
            INSERT INTO squads
            (room_id, squad_number)
            VALUES (?, ?)
        """, (room_id, next_number))

        conn.commit()
        return cursor.lastrowid


def get_available_squad(room_id):
    with closing(get_connection()) as conn:
        squads = conn.execute("""
            SELECT *
            FROM squads
            WHERE room_id = ?
            ORDER BY squad_number ASC
        """, (room_id,)).fetchall()

        for squad in squads:
            count = conn.execute("""
                SELECT COUNT(*) AS count
                FROM registrations
                WHERE squad_id = ?
                AND status = 'active'
            """, (squad["id"],)).fetchone()["count"]

            if count < 4:
                return squad

    return None


def register_player(telegram_id, room_id):
    with closing(get_connection()) as conn:

        user = conn.execute("""
            SELECT id FROM users
            WHERE telegram_id = ?
        """, (telegram_id,)).fetchone()

        if not user:
            return False, "user_not_found"

        existing = conn.execute("""
            SELECT id
            FROM registrations
            WHERE user_id = ?
            AND room_id = ?
            AND status = 'active'
        """, (user["id"], room_id)).fetchone()

        if existing:
            return False, "already_registered"

        room = conn.execute("""
            SELECT *
            FROM rooms
            WHERE id = ?
        """, (room_id,)).fetchone()

        if not room:
            return False, "room_not_found"

        count = conn.execute("""
            SELECT COUNT(*) AS count
            FROM registrations
            WHERE room_id = ?
            AND status = 'active'
        """, (room_id,)).fetchone()["count"]

        if count >= room["capacity"]:
            return False, "room_full"

        squad = get_available_squad(room_id)

        if not squad:
            cursor = conn.execute("""
                SELECT MAX(squad_number) AS max_number
                FROM squads
                WHERE room_id = ?
            """, (room_id,))

            max_number = cursor.fetchone()["max_number"] or 0

            conn.execute("""
                INSERT INTO squads
                (room_id, squad_number)
                VALUES (?, ?)
            """, (room_id, max_number + 1))

            squad = conn.execute("""
                SELECT *
                FROM squads
                WHERE room_id = ?
                AND squad_number = ?
            """, (room_id, max_number + 1)).fetchone()

        conn.execute("""
            INSERT INTO registrations
            (user_id, room_id, squad_id)
            VALUES (?, ?, ?)
        """, (
            user["id"],
            room_id,
            squad["id"]
        ))

        conn.commit()

        return True, squad["squad_number"]


def cancel_registration(telegram_id, room_id):
    with closing(get_connection()) as conn:

        user = conn.execute("""
            SELECT id
            FROM users
            WHERE telegram_id = ?
        """, (telegram_id,)).fetchone()

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
        """, (room_id,)).fetchone()

        conn.execute("""
            UPDATE registrations
            SET status = 'cancelled'
            WHERE id = ?
        """, (registration["id"],))

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
            (user_id, amount, type, description)
            VALUES (?, ?, ?, ?)
        """, (
            user["id"],
            room["entry_fee"],
            "cancel_refund",
            "Refund after cancellation"
        ))

        conn.commit()

        return True


# Initialize database when imported
init_db()
