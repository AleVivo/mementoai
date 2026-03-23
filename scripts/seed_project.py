"""
seed_project.py — Inserisce il progetto di test e i suoi membri.
"""

from datetime import datetime, timedelta, timezone
from bson import ObjectId

NOW = datetime.now(timezone.utc)

def weeks_ago(n: int) -> datetime:
    return NOW - timedelta(weeks=n)


TEST_PROJECT = {
    "name": "shopflow",
    "description": "Piattaforma e-commerce del team Shopflow.",
}


async def run(
    db,
    user_ids: dict[str, ObjectId],
    user_names: dict[str, str],
) -> ObjectId:
    """Restituisce il project_id."""
    owner_id = user_ids.get("alex")
    if not owner_id:
        raise RuntimeError("Utente 'alex' non trovato — impossibile creare il progetto.")

    existing = await db.projects.find_one({"name": TEST_PROJECT["name"]})
    if existing:
        project_id = existing["_id"]
        print(f"ℹ️  Progetto '{TEST_PROJECT['name']}' già presente — skip")
    else:
        result = await db.projects.insert_one({
            "name": TEST_PROJECT["name"],
            "description": TEST_PROJECT["description"],
            "ownerId": owner_id,
            "createdAt": weeks_ago(20),
        })
        project_id = result.inserted_id
        print(f"✅ Progetto creato: '{TEST_PROJECT['name']}' (id: {project_id})")

    for key, uid in user_ids.items():
        role = "owner" if key == "alex" else "member"
        existing_member = await db.project_members.find_one(
            {"projectId": project_id, "userId": uid}
        )
        if existing_member:
            print(f"ℹ️  {user_names.get(key, key)} già membro — skip")
        else:
            await db.project_members.insert_one({
                "projectId": project_id,
                "userId": uid,
                "role": role,
                "addedAt": weeks_ago(20),
            })
            print(f"✅ Membro aggiunto: {user_names.get(key, key)} ({role})")

    return project_id