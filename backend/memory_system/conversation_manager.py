import json
import uuid

from pathlib import Path
from datetime import datetime


class ConversationManager:

    def __init__(
        self,
        persist=True
    ):

        self.persist = persist

        self.file = Path(
            "data/memory/conversations.json"
        )

        if self.persist:

            self.file.parent.mkdir(
                parents=True,
                exist_ok=True
            )


            if self.file.exists():

                try:

                    self.data = json.loads(
                        self.file.read_text(
                            encoding="utf-8"
                        )
                    )

                except (
                    json.JSONDecodeError,
                    OSError
                ):

                    self.data = {
                        "users": {}
                    }

            else:

                self.data = {
                    "users": {}
                }

        else:

            # Completely temporary memory.
            # Nothing gets written to disk.

            self.data = {
                "users": {}
            }


        if "users" not in self.data:

            self.data["users"] = {}


        self.save()


    # =====================================
    # SAVE
    # =====================================

    def save(self):

        if not self.persist:
            return

        self.file.write_text(

            json.dumps(
                self.data,
                indent=4,
                ensure_ascii=False
            ),

            encoding="utf-8"
        )


    # =====================================
    # USER
    # =====================================

    def _user(
        self,
        email
    ):

        email = (
            email
            .strip()
            .lower()
        )


        if email not in self.data["users"]:

            self.data["users"][email] = {
                "conversations": {}
            }


        return self.data["users"][email]


    # =====================================
    # CREATE
    # =====================================

    def create(
        self,
        email
    ):

        user = self._user(
            email
        )


        cid = str(
            uuid.uuid4()
        )


        now = (
            datetime.now()
            .isoformat()
        )


        user[
            "conversations"
        ][cid] = {

            "id":
                cid,

            "title":
                "New Chat",

            "created_at":
                now,

            "updated_at":
                now,

            "messages":
                []

        }


        self.save()


        return cid


    # =====================================
    # LIST
    # =====================================

    def list(
        self,
        email
    ):

        user = self._user(
            email
        )


        conversations = (
            user["conversations"]
        )


        return dict(
            sorted(
                conversations.items(),
                key=lambda item:
                    item[1].get(
                        "updated_at",
                        ""
                    ),
                reverse=True
            )
        )


    # =====================================
    # ADD MESSAGE
    # =====================================

    def add_message(
        self,
        email,
        cid,
        role,
        text
    ):

        user = self._user(
            email
        )


        if cid not in user[
            "conversations"
        ]:

            return False


        conversation = (
            user[
                "conversations"
            ][cid]
        )


        conversation[
            "messages"
        ].append({

            "role":
                role,

            "text":
                text,

            "timestamp":
                datetime.now()
                .isoformat()

        })


        conversation[
            "updated_at"
        ] = (
            datetime.now()
            .isoformat()
        )


        if (
            role == "user"
            and
            conversation[
                "title"
            ] == "New Chat"
        ):

            conversation[
                "title"
            ] = self.generate_title(
                text
            )


        self.save()


        return True


    # =====================================
    # TITLE
    # =====================================

    def generate_title(
        self,
        message
    ):

        title = (
            message
            .strip()
            .replace(
                "\n",
                " "
            )
        )


        if not title:

            return "New Chat"


        title = " ".join(
            title.split()
        )


        max_length = 45


        if len(title) > max_length:

            title = (
                title[:max_length]
                .rstrip()
                + "..."
            )


        return title


    # =====================================
    # GET
    # =====================================

    def get(
        self,
        email,
        cid
    ):

        user = self._user(
            email
        )


        return user[
            "conversations"
        ].get(cid)


    # =====================================
    # RENAME
    # =====================================

    def rename(
        self,
        email,
        cid,
        title
    ):

        user = self._user(
            email
        )


        if cid not in user[
            "conversations"
        ]:

            return False


        title = (
            title
            .strip()
            .replace(
                "\n",
                " "
            )
        )


        if not title:

            return False


        conversation = (
            user[
                "conversations"
            ][cid]
        )


        conversation[
            "title"
        ] = title


        conversation[
            "updated_at"
        ] = (
            datetime.now()
            .isoformat()
        )


        self.save()


        return True


    # =====================================
    # DELETE
    # =====================================

    def delete(
        self,
        email,
        cid
    ):

        user = self._user(
            email
        )


        if cid not in user[
            "conversations"
        ]:

            return False


        del user[
            "conversations"
        ][cid]


        self.save()


        return True