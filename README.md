<div align="center">
  <h1>GitHub PR to GitLab MR Sync (GitHub Action)</h1>
</div>

Sync approved GitHub PRs to an internal GitLab codebase as Merge Requests.

---

- [Workflow Overview](#workflow-overview)
  - [Workflow File](#workflow-file)
  - [Inputs](#inputs)
- [Steps to Sync a PR](#steps-to-sync-a-pr)
- [Project Issues](#project-issues)
- [Contributing](#contributing)

## Workflow Overview

This GitHub Action synchronizes pull requests from GitHub to an internal
GitLab instance. When a maintainer approves a PR by adding a label, the
action creates a corresponding branch and MR on GitLab.

To use this action you need:

- A workflow file
- Issue/PR labels: `PR-Sync-Merge`, `PR-Sync-Rebase`, `PR-Sync-Update`
- Action secrets

### Workflow File

```yaml
# FILE: .github/workflows/pr_approved.yml

name: Sync approved PRs to internal codebase
on:
  pull_request_target:
    types: [labeled]

jobs:
  sync_prs:
    name: GitHub PR to GitLab MR Sync
    runs-on: ubuntu-latest
    if: contains(fromJSON('["PR-Sync-Merge","PR-Sync-Rebase","PR-Sync-Update"]'), github.event.label.name)
    steps:
      - uses: actions/checkout@v4

      - name: Sync PR to GitLab
        uses: <your-org>/sync-pr-to-gitlab@v2
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          gitlab_url: ${{ secrets.GITLAB_URL }}
          gitlab_token: ${{ secrets.GITLAB_TOKEN }}
          git_config_name: ${{ secrets.GIT_CONFIG_NAME }}
          git_config_email: ${{ secrets.GIT_CONFIG_EMAIL }}
          # gitlab_namespace: MY_GROUP  # optional, defaults to GitHub org name
```

### Inputs

| Input              | Description                                                    | Required |
| ------------------ | -------------------------------------------------------------- | -------- |
| `github_token`     | GitHub token for API access                                    | Yes      |
| `gitlab_url`       | GitLab instance host (e.g. `gitlab.example.com`)               | Yes      |
| `gitlab_token`     | GitLab API access token                                        | Yes      |
| `git_config_name`  | Git user.name for rebase commits                               | Yes      |
| `git_config_email` | Git user.email for rebase commits                              | Yes      |
| `gitlab_namespace` | GitLab namespace/group (defaults to GitHub org name)           | No       |

## Steps to Sync a PR

1. Apply one of the following labels:
   - `PR-Sync-Merge` — create an internal MR from the PR branch head.
   - `PR-Sync-Rebase` — rebase the PR onto the latest base branch before creating the MR.
   - `PR-Sync-Update` — force-push new commits to an existing internal branch.
2. The action automatically uses `pull_request.head.sha` from the label event and validates it against the current PR HEAD before sync.
3. On successful sync, the action updates a managed PR comment with sync metadata (mode, SHA, target branch, trigger user, timestamp). On later updates, the previous managed comment is replaced.

> Only contributors with [TRIAGE](https://docs.github.com/en/organizations/managing-access-to-your-organizations-repositories/repository-permission-levels-for-an-organization#permission-levels-for-repositories-owned-by-an-organization) access or higher can apply labels.
> If new commits are pushed after labeling, the workflow fails by design. Remove/re-apply the label to sync the latest reviewed commit.

## Project Issues

If you encounter any issues, feel free to report them in the project's issues or create a Pull Request with your suggestion.

## Contributing

If you are interested in contributing to this project, see the [Contributing Guide](CONTRIBUTING.md).
