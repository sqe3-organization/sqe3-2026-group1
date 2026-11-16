"""Authentication tests for POST /gists.
These tests check that a Gist cannot be created using an invalid token.
The test without a token is covered in test_gists_post.py (TC_GIST_POST_002).
"""

import pytest

from config.settings import Endpoints
from core.assertions import assert_error


@pytest.mark.negative
@pytest.mark.no_token
def test_tc_gist_auth_001_verify_that_a_gist_cannot_be_created_with_an_invalid_token(invalid_client):
    new_gist = {
        "description": "Must not be created",
        "public": False,
        "files": {"hello.txt": {"content": "Invalid token"}}
    }

    response = invalid_client.post(Endpoints.GISTS, json=new_gist)

    assert_error(response, 401, "Bad credentials")