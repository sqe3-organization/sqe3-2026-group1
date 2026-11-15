"""Same JSON schemas used in the Postman collection (issueSchema / errorSchema)."""

ISSUE_SCHEMA = {
    "type": "object",
    "required": ["id", "number", "title", "state", "user", "labels", "assignees", "locked", "created_at", "html_url"],
    "properties": {
        "id": {"type": "integer"},
        "number": {"type": "integer"},
        "title": {"type": "string"},
        "body": {"type": ["string", "null"]},
        "state": {"type": "string", "enum": ["open", "closed"]},
        "state_reason": {"type": ["string", "null"]},
        "user": {"type": "object", "required": ["login"], "properties": {"login": {"type": "string"}}},
        "labels": {"type": "array"},
        "assignees": {"type": "array"},
        "locked": {"type": "boolean"},
        "created_at": {"type": "string"},
        "html_url": {"type": "string"},
    },
}

ERROR_SCHEMA = {
    "type": "object",
    "required": ["message", "documentation_url"],
    "properties": {
        "message": {"type": "string"},
        "documentation_url": {"type": "string"},
    },
}
