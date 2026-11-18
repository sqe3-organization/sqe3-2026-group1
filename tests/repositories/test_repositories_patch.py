"""PATCH /repos/{owner}/{repo} (folder 03_PATCH_Update_Repo of the Postman collection): the case that needs no repository.

The other PATCH cases create their own repository through a fixture and come in the next block."""
import pytest

from config import settings
from config.settings import Endpoints
from core.assertions import assert_error


@pytest.mark.negative
def test_tc_repo_patch_005_verify_that_patching_a_non_existent_repo_returns_404(github):
    response = github.patch(Endpoints.repository(settings.NON_EXISTENT_REPO), json={"description": "testing non-existent repo"})

    assert_error(response, 404, "Not Found")
