## Unreleased

- feat: remove manual `sha=` comment requirement and use PR event `head.sha` by default
- feat: auto-maintain structured PR sync-status comment after successful merge/rebase/update
- change: fail sync when label-event SHA no longer matches current PR HEAD; re-apply label after new pushes

## v1.0.0 (2024-03-27)


- docs: update CONTRIBUTING.md, usage of requirements.txt
- ci: add pre-commit CI job
- docs: update README, add CONTRIBUTING Guide
- change(dockerfile): refactored Dockerfile, python alpine base image
- ci: project by pyproject.toml, pre-commit hooks, refactor Python
- ci(danger-github): add dangerjs workflow to the project
- init: copy the code from the espressif/github-actions repo

## v0.1.0 (2024-02-19)


- Init
