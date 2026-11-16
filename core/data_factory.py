"""Random test data so runs never collide ({{$randomProductName}} in Postman)."""
import uuid

from faker import Faker

fake = Faker()


def issue_title(tc_id):
    return f"{tc_id} - {fake.catch_phrase()}"


def issue_body():
    return fake.sentence()


def long_text(length):
    return "x" * length

def _short_id(tc_id):
    """tc_label_post_001" -> "label-post-001" (names stay under the 50 characters of a label)."""
    return tc_id.lower().replace("tc_", "", 1).replace("_", "-")


def label_name(tc_id):
    """Every test label starts with qa-pm- so the session cleanup can find leftovers."""
    return f"qa-pm-{_short_id(tc_id)}-{uuid.uuid4().hex[:6]}"


def milestone_title(tc_id):
    return f"qa-pm-{_short_id(tc_id)}-{uuid.uuid4().hex[:6]}"


def description(length):
    return "a" * length

def gist_description(tc_id):
    """Every test Gist starts with qa-pm- so the session cleanup can find leftovers."""
    return f"qa-pm-{_short_id(tc_id)}-{uuid.uuid4().hex[:6]}"


def file_content():
    return fake.paragraph(nb_sentences=2)
