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
            status TEXT NOT NULL DEFAULT 'active',
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
# GET ROOMS
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
    third_prize=None,
    status=None
):

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

    if capacity is not None:
        fields.append("capacity = ?")
        values.append(capacity)

    if entry_fee is not None:
        fields.append("entry_fee = ?")
        values.append(entry_fee)

    if kill_prize is not None:
        fields.append("kill_prize = ?")
        values.append(kill_prize)

    if first_prize is not None:
        fields.append("first_prize = ?")
        values.append(first_prize)

    if second_prize is not None:
        fields.append("second_prize = ?")
        values.append(second_prize)

    if third_prize is not None:
        fields.append("third_prize = ?")
        values.append(third_prize)

    if status is not None:
        fields.append("status = ?")
        values.append(status)

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
# DELETE ROOM
# =========================================================

def delete_room(room_id):

    with closing(get_connection()) as conn:

        conn.execute("""
            DELETE FROM rooms
            WHERE id = ?
        """, (
            room_id,
        ))

        conn.commit()


# =========================================================
# RESET ROOM
# =========================================================

def reset_room(room_id):

    with closing(get_connection()) as conn:

        conn.execute("""
            DELETE FROM registrations
            WHERE room_id = ?
        """, (
            room_id,
        ))

        conn.execute("""
            DELETE FROM squads
            WHERE room_id = ?
        """, (
            room_id,
        ))

        conn.commit()


# =========================================================
# ROOM PLAYER COUNT
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


# =========================================================
# ROOM REVENUE
# =========================================================

def get_room_revenue(room_id):

    room = get_room(room_id)

    if not room:
        return 0

    players = get_room_player_count(room_id)

    return players * room["entry_fee"]


# =========================================================
# ROOM PRIZES
# =========================================================

def get_room_total_prizes(room_id):

    room = get_room(room_id)

    if not room:
        return 0

    players = get_room_player_count(room_id)

    kill_prizes = (
        players * room["kill_prize"]
    )

    team_prizes = (
        room["first_prize"]
        + room["second_prize"]
        + room["third_prize"]
    )

    return kill_prizes + team_prizes


# =========================================================
# ROOM PROFIT
# =========================================================

def get_room_profit(room_id):

    revenue = get_room_revenue(room_id)

    prizes = get_room_total_prizes(room_id)

    return revenue - prizes


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
# REGISTER PLAYER
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
            AND status = 'open'
        """, (
            room_id,
        )).fetchone()

        if not room:
            return False, "room_not_found"


        player_count = conn.execute("""
            SELECT COUNT(*) AS count
            FROM registrations
            WHERE room_id = ?
            AND status = 'active'
        """, (
            room_id,
        )).fetchone()["count"]


        if player_count >= room["capacity"]:
            return False, "room_full"


        squad = None

        squads = conn.execute("""
            SELECT *
            FROM squads
            WHERE room_id = ?
            ORDER BY squad_number ASC
        """, (
            room_id,
        )).fetchall()


        for item in squads:

            count = conn.execute("""
                SELECT COUNT(*) AS count
                FROM registrations
                WHERE squad_id = ?
                AND status = 'active'
            """, (
                item["id"],
            )).fetchone()["count"]

            if count < 4:

                squad = item
                break


        if not squad:

            max_number = conn.execute("""
                SELECT MAX(squad_number) AS max_number
                FROM squads
                WHERE room_id = ?
            """, (
                room_id,
            )).fetchone()["max_number"]

            next_number = (
                max_number or 0
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


            squad = conn.execute("""
                SELECT *
                FROM squads
                WHERE id = ?
            """, (
                cursor.lastrowid,
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

        if not room:
            return False


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

                rooms.id AS room_id,

                rooms.name AS room_name,

                rooms.room_date,

                rooms.room_time,

                rooms.capacity,

                rooms.entry_fee,

                rooms.kill_prize,

                rooms.first_prize,

                rooms.second_prize,

                rooms.third_prize,

                squads.squad_number

            FROM registrations

            JOIN users
                ON users.id = registrations.user_id

            JOIN rooms
                ON rooms.id = registrations.room_id

            LEFT JOIN squads
                ON squads.id = registrations.squad_id

            WHERE users.telegram_id = ?

            AND registrations.status = 'active'

            ORDER BY registrations.id DESC

        """, (
            telegram_id,
        )).fetchall()


# =========================================================
# USER ROOMS
# =========================================================

def get_user_rooms(telegram_id):

    return get_user_matches(telegram_id)


# =========================================================
# INITIALIZE
# =========================================================

init_db()
