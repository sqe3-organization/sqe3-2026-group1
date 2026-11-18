"""DELETE /repos/{owner}/{repo} (folder 04_DELETE_Delete_Repo of the Postman collection): the case that needs no repository.

The path points to a repository that does not exist, so this test can never delete a real one.
The other DELETE cases create their own repository through a fixture and come in the next block."""
import pytest

from config import settings
from config.settings import Endpoints
from core.assertions import assert_error


@pytest.mark.negative
def test_tc_repo_delete_004_verify_that_deleting_a_non_existent_repo_returns_404(github):
    response = github.delete(Endpoints.repository(settings.NON_EXISTENT_REPO))

    assert_error(response, 404, "Not Found")
