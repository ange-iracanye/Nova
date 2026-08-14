import uuid
from datetime import datetime, timezone


def now():

    return datetime.now(
        timezone.utc
    ).isoformat()


def memory_id():

    return str(
        uuid.uuid4()
    )


def create_memory(
    memory_type,
    content,
    importance=50,
    subject=None,
    source=None,
    confidence=1.0
):

    return {

        "id":
            memory_id(),

        "type":
            memory_type,

        "content":
            content,

        "subject":
            subject,

        "source":
            source,

        "importance":
            importance,

        "confidence":
            confidence,

        "created_at":
            now(),

        "updated_at":
            now(),

        "last_accessed":
            None,

        "access_count":
            0,

        "reinforced":
            0
    }