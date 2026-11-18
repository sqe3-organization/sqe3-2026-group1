"""Values of the Postman environment "GitHub Issues - SQE3", now read from .env."""
import os
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("API_BASE_URL", "https://api.github.com")
API_VERSION = os.getenv("API_VERSION", "2026-03-10")
TOKEN = os.getenv("GITHUB_TOKEN", "")
OWNER = os.getenv("OWNER", "lucasgabrieldls")
REPO = os.getenv("REPO", "sqe3-issues-test")
PUBLIC_OWNER = os.getenv("PUBLIC_OWNER", "octocat")
PUBLIC_REPO = os.getenv("PUBLIC_REPO", "Hello-World")
MAX_RESPONSE_TIME_MS = int(os.getenv("MAX_RESPONSE_TIME_MS", "2000"))

# Repositories module: the read-only tests use a private repository of OWNER (readRepo in Postman)
READ_REPO = os.getenv("READ_REPO", "")
TOKEN_REPO_ONLY = os.getenv("TOKEN_REPO_ONLY", "")  # classic token with the repo scope only
TOKEN_NO_ADMIN = os.getenv("TOKEN_NO_ADMIN", "")  # fine-grained token without Administration
REPO_PAUSE_SECONDS = float(os.getenv("REPO_PAUSE_SECONDS", "2"))  # pause after tests that create repositories

# Test data that does not change between runs (collection variables in Postman)
INVALID_TOKEN = "ghp_thisTokenIsInvalid000000000000000000"
NON_EXISTENT_ISSUE = 999999999
NON_EXISTENT_MILESTONE = 999999999
NON_EXISTENT_REPO = "repo-that-does-not-exist-xyz"
NON_EXISTENT_GIST = "123456789abcdef123456789"
LOCK_REASONS = ["off-topic", "too heated", "resolved", "spam"]
TEST_REPO_PREFIX = "qa-pm-"  # cleanup deletes only repositories whose name starts with this


class Endpoints:
    USER = "/user"
    ISSUES = f"/repos/{OWNER}/{REPO}/issues"
    PUBLIC_REPOSITORY = f"/repos/{PUBLIC_OWNER}/{PUBLIC_REPO}"
    PUBLIC_ISSUES = f"{PUBLIC_REPOSITORY}/issues"
    LABELS = f"/repos/{OWNER}/{REPO}/labels"
    MILESTONES = f"/repos/{OWNER}/{REPO}/milestones"
    PUBLIC_LABELS = f"{PUBLIC_REPOSITORY}/labels"
    PUBLIC_MILESTONES = f"{PUBLIC_REPOSITORY}/milestones"
    GISTS = "/gists"
    PUBLIC_GISTS = "/gists/public"
    USER_REPOS = "/user/repos"
    READ_REPOSITORY = f"/repos/{OWNER}/{READ_REPO}"

    @staticmethod
    def issue(number):
        return f"/repos/{OWNER}/{REPO}/issues/{number}"

    @staticmethod
    def issue_lock(number):
        return f"/repos/{OWNER}/{REPO}/issues/{number}/lock"

    @staticmethod
    def label(name):
        """Label names can have spaces, so the name is URL-encoded."""
        return f"/repos/{OWNER}/{REPO}/labels/{quote(name, safe='')}"

    @staticmethod
    def milestone(number):
        return f"/repos/{OWNER}/{REPO}/milestones/{number}"

    @staticmethod
    def gist(gist_id):
        return f"/gists/{gist_id}"

    @staticmethod
    def repository(name):
        return f"/repos/{OWNER}/{name}"
