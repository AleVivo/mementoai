"""
seed.py — Entry point principale del seed.

Uso:
    python scripts/seed.py                    # inserisce (skip se già presenti)
    python scripts/seed.py --reset            # pulisce tutto e reinserisce
    python scripts/seed.py --reset --no-user  # reinserisce tutto tranne utenti

Avvio dalla root del progetto.
"""

import asyncio
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from app.config import settings
from pymongo import AsyncMongoClient

import seed_users
import seed_project
import seed_entries
import seed_config


async def seed(reset: bool = False, skip_user: bool = False) -> None:
    client = AsyncMongoClient(
        settings.mongodb_url,
        username=settings.mongodb_user,
        password=settings.mongodb_password,
        directConnection=True,
    )
    db = client[settings.mongodb_db]

    try:
        print(f"\n🌱 MementoAI Seed — DB: {settings.mongodb_db}")
        print(f"   MongoDB: {settings.mongodb_url}\n")

        # ── Reset ────────────────────────────────────────────────────────────
        if reset:
            collections = ["entries", "chunks", "projects", "project_members"]
            if not skip_user:
                collections.append("users")
            for coll in collections:
                r = await db[coll].delete_many({})
                print(f"🗑  Cancellati {r.deleted_count} documenti da '{coll}'")
            print()

        # ── Config ───────────────────────────────────────────────────────────
        print("── Config ──────────────────────────────────────")
        await seed_config.run(db, reset=reset)
        print()

        # ── Utenti ───────────────────────────────────────────────────────────
        if not skip_user:
            print("── Utenti ──────────────────────────────────────")
            user_ids, user_names = await seed_users.run(db, reset=reset)
            print()
        else:
            # Recupera utenti esistenti senza inserirli
            user_ids, user_names = await seed_users.run(db, reset=False)

        # ── Indice vettoriale ────────────────────────────────────────────────
        print("── Indice vettoriale ───────────────────────────")
        await seed_config.ensure_vector_index(db)
        print()

        # ── Progetto ─────────────────────────────────────────────────────────
        print("── Progetto ────────────────────────────────────")
        project_id = await seed_project.run(db, user_ids, user_names)
        print()

        # ── Entry ─────────────────────────────────────────────────────────────
        print("── Entry ───────────────────────────────────────")
        await seed_entries.run(db, project_id, user_ids, user_names)
        print()

        # ── Riepilogo ────────────────────────────────────────────────────────
        print("✅ Seed completato!")
        print(f"\n   Progetto : shopflow (id: {project_id})")
        for u in seed_users.TEST_USERS:
            print(f"   Login    : {u['email']} / {u['password']} ({u['role']})")
        print(f"\n   ⚠ Le entry sono vector_status='pending'.")
        print(f"   Usa [Indicizza] nell'editor per vettorializzarle.")

    finally:
        await client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Popola il DB di MementoAI con dati di test.")
    parser.add_argument("--reset", action="store_true", help="Cancella i dati esistenti prima di inserire")
    parser.add_argument("--no-user", action="store_true", dest="no_user", help="Non tocca la collection users")
    args = parser.parse_args()
    asyncio.run(seed(reset=args.reset, skip_user=args.no_user))


if __name__ == "__main__":
    main()