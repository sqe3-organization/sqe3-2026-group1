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

LABEL_SCHEMA = {
    "type": "object",
    "required": ["id", "name", "color", "default", "description"],
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "color": {"type": "string"},
        "default": {"type": "boolean"},
        "description": {"type": ["string", "null"]},
    },
}

MILESTONE_SCHEMA = {
    "type": "object",
    "required": ["number", "title", "state", "url"],
    "properties": {
        "number": {"type": "integer"},
        "title": {"type": "string"},
        "state": {"type": "string", "enum": ["open", "closed"]},
        "url": {"type": "string"},
        "description": {"type": ["string", "null"]},
        "due_on": {"type": ["string", "null"]},
        "closed_at": {"type": ["string", "null"]},
    },
}

GIST_SCHEMA = {
    "type": "object",
    "required": ["id", "url", "html_url", "public", "description", "files"],
    "properties": {
        "id": {"type": "string"},
        "url": {"type": "string"},
        "html_url": {"type": "string"},
        "public": {"type": "boolean"},
        "description": {"type": ["string", "null"]},
        "files": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "content": {"type": "string"},
                    "size": {"type": "integer"},
                },
            },
        },
    },
}
