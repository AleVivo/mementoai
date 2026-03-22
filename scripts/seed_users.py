"""
seed_users.py — Inserisce gli utenti di test.
"""

from datetime import datetime, timedelta, timezone
from bson import ObjectId
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

password_hasher = PasswordHash([Argon2Hasher()])

NOW = datetime.now(timezone.utc)

def weeks_ago(n: int) -> datetime:
    return NOW - timedelta(weeks=n)


TEST_USERS = [
    {
        "email": "alex@memento.com",
        "password": "memento123",
        "first_name": "Alex",
        "last_name": "Rossi",
        "company": "Shopflow Team",
        "role": "admin",
    },
    {
        "email": "marco@memento.com",
        "password": "memento123",
        "first_name": "Marco",
        "last_name": "Bianchi",
        "company": "Shopflow Team",
        "role": "user",
    },
]


async def run(
    db,
    reset: bool = False,
) -> tuple[dict[str, ObjectId], dict[str, str]]:
    """
    Restituisce:
    - user_ids:   { "alex": ObjectId(...), "marco": ObjectId(...) }
    - user_names: { "alex": "Alex Rossi",  "marco": "Marco Bianchi" }
    """
    user_ids: dict[str, ObjectId] = {}
    user_names: dict[str, str] = {}

    for u in TEST_USERS:
        key = u["first_name"].lower()
        existing = await db.users.find_one({"email": u["email"]})

        if existing:
            user_ids[key] = existing["_id"]
            user_names[key] = f"{u['first_name']} {u['last_name']}"
            print(f"ℹ️  Utente {u['email']} già presente — skip")
        else:
            hashed = password_hasher.hash(u["password"])
            doc = {
                "email": u["email"],
                "hashed_password": hashed,
                "first_name": u["first_name"],
                "last_name": u["last_name"],
                "company": u["company"],
                "role": u["role"],
                "created_at": weeks_ago(20),
            }
            result = await db.users.insert_one(doc)
            user_ids[key] = result.inserted_id
            user_names[key] = f"{u['first_name']} {u['last_name']}"
            print(f"✅ Utente creato: {u['email']} ({u['role']}) / {u['password']}")

    return user_ids, user_names