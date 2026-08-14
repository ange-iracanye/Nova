import json
import hashlib
from pathlib import Path


USERS_FILE = Path("data/users.json")


def load_users():

    USERS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if not USERS_FILE.exists():

        USERS_FILE.write_text(
            json.dumps(
                {"users": {}},
                indent=4
            ),
            encoding="utf-8"
        )

    try:

        return json.loads(
            USERS_FILE.read_text(
                encoding="utf-8"
            )
        )

    except Exception:

        return {"users": {}}


def save_users(data):

    USERS_FILE.write_text(
        json.dumps(
            data,
            indent=4,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


def hash_password(password):

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def register_user(email, password):

    email = email.strip().lower()

    data = load_users()

    if email in data["users"]:
        return False

    data["users"][email] = {
        "email": email,
        "password": hash_password(password)
    }

    save_users(data)

    return True


def login_user(email, password):

    email = email.strip().lower()

    data = load_users()

    user = data["users"].get(email)

    if not user:
        return False

    return (
        user["password"]
        == hash_password(password)
    )