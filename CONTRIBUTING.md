# Contributing

This file describes how our team works in this repository. The project contains automated API tests for the GitHub REST API (Issues, Gists, Repositories, Search, Labels and Milestones). The tests exist as Postman collections and are being migrated to Python.

> **Note on branch protection.** Our team cannot configure the protection rules of `main` (our role has no access to the branch settings). The rules below are therefore a **team agreement** that every member follows, not rules enforced by GitHub.

## Summary of the workflow

1. Pick or create a ticket (a GitHub issue).
2. Create a short-lived branch from `main` named `type/TICKET-<number>-short-description`.
3. Commit your work with Conventional Commits and the ticket reference.
4. Push the branch and open a Pull Request to `main`.
5. Get at least one approval from another team member and make sure the checks pass.
6. Merge with **Squash and merge** and delete the branch.

Nothing is pushed directly to `main`. Every change reaches `main` through a Pull Request.

## Tickets

Every piece of work has a ticket. The ticket number is the number of the GitHub issue: `TICKET-2` is issue `#2`.

## Branches

- `main` is the only long-lived branch. There is no `develop` branch.
- Everyone works on a local short-lived branch created from `main`.
- Branch names must identify the type of work and include the ticket number:

  `type/TICKET-<number>-short-description`

| Type | Use | Example |
|---|---|---|
| `feature` | New functionality or test coverage | `feature/TICKET-5-add-label-tests` |
| `bugfix` | Correction of an existing defect | `bugfix/TICKET-6-fix-milestone-validation` |
| `hotfix` | Urgent correction | `hotfix/TICKET-7-fix-authentication-check` |
| `docs` | Documentation changes | `docs/TICKET-2-add-contributing-guide` |
| `refactor` | Code changes that do not change behavior | `refactor/TICKET-8-simplify-response-checks` |
| `release` | Release preparation. It uses the version number instead of a ticket | `release/v1.2.0` |

Use lowercase letters and hyphens. Delete the branch after its Pull Request is merged.

## Commits

Commit messages follow the [Conventional Commits](https://www.conventionalcommits.org/) specification and include the ticket reference:

```
type(scope): short description [TICKET-<number>]
```

| Type | Use |
|---|---|
| `feat` | New functionality or new test coverage |
| `fix` | Correction of a defect in existing code or tests |
| `docs` | Documentation changes |
| `test` | Adding or modifying tests |
| `refactor` | Code restructuring without changing behavior |
| `chore` | Maintenance, dependencies or configuration |

Examples:

```
feat(labels): add label creation tests [TICKET-5]
fix(milestones): correct invalid date validation [TICKET-6]
docs(contributing): add team conventions guide [TICKET-2]
test(issues): cover missing title validation [TICKET-9]
refactor(auth): centralize token handling [TICKET-8]
chore(deps): update development dependencies [TICKET-10]
```

Use the imperative mood, keep the description short, and make one logical change per commit. Avoid vague messages such as `update` or `fix stuff`.

## Pull Requests

### Title

The title follows the same format as a commit message, because the team uses squash merge and the title becomes the commit on `main`:

```
type(scope): short description [TICKET-<number>]
```

Example: `docs(contributing): add team conventions guide [TICKET-2]`

### Description

Every Pull Request includes:

```markdown
## What changed?
Describe the changes.

## Why?
Explain the purpose and reference the ticket (for example, Closes #2).

## How to test?
Commands or steps to verify the changes.

## Test results
Checks executed and their results.
```

### Review and merge rules

- The Pull Request targets `main`.
- At least **one team member must approve** it before merging.
- The author does not approve their own Pull Request.
- Reviewers check correctness, readability, test coverage, ticket references and that no secrets are exposed.
- All requested changes and conversations are resolved before merging.
- There are no merge conflicts with `main`.
- The CI checks pass, once the pipeline exists (see below).
- Use **Squash and merge**. The squash commit follows the Conventional Commits format and includes the ticket reference. Check the commit message in the merge dialog before confirming.
- Do not push directly to `main` and do not force push.

## Continuous Integration and Continuous Testing

The team plans to use Continuous Integration (CI) and Continuous Testing (CT). Continuous Delivery and Deployment are not part of this workflow. The Python tools below are **examples**: the team will confirm them when the code tools are chosen.

**CI** runs on every push to a Pull Request:

| Stage | Purpose | Example tool |
|---|---|---|
| Dependency installation | Install the dependencies in a clean environment | `pip` |
| Linting | Detect style problems and common errors | `Ruff` |
| Formatting check | Check formatting without changing files | `Black --check` |
| Static analysis | Detect typing problems before execution | `mypy` |
| Security analysis | Detect known vulnerable dependencies | `pip-audit` |
| Unit tests | Test functions that do not use the real API | `pytest` |

**CT** runs when a change is merged into `main`:

| Stage | Purpose | Example tool |
|---|---|---|
| Smoke tests | Check that the API is reachable and basic requests work | `pytest` |
| Functional tests | Validate the expected behavior of the endpoints | `pytest` |
| Negative tests | Check invalid input, missing credentials and nonexistent resources | `pytest` |
| Boundary tests | Check limits, such as maximum lengths and pagination | `pytest` |
| Test reporting | Generate a report of the results | `pytest-html` |

Tests that modify real GitHub resources use a dedicated test repository and clean up what they create. Because the team cannot configure branch protection, the CI checks inform the review but cannot block a merge: reviewers must check them before approving.

## Additional conventions

- **Secrets:** never commit API tokens or credentials. Keep local secrets in a `.env` file that is listed in `.gitignore`, and store the pipeline's credentials in GitHub's secrets storage (Settings, Secrets and variables, Actions).
- **Test naming:** use `test_*.py` for test files and `test_*` for test functions, grouped by API feature, for example `test_labels.py` and `test_milestones.py`.
- **Test reports:** keep generated reports as CI artifacts and do not commit temporary execution results to the repository, unless a report is a required deliverable.