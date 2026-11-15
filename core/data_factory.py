"""Random test data so runs never collide ({{$randomProductName}} in Postman)."""
from faker import Faker

fake = Faker()


def issue_title(tc_id):
    return f"{tc_id} - {fake.catch_phrase()}"


def issue_body():
    return fake.sentence()


def long_text(length):
    return "x" * length
