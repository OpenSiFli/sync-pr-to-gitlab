from __future__ import annotations

import json
import os

from gitlab.exceptions import GitlabGetError

from sync_pr_to_gitlab.config import Config
from sync_pr_to_gitlab.git_ops import checkout_pr_branch
from sync_pr_to_gitlab.git_ops import fetch_pr
from sync_pr_to_gitlab.git_ops import push_to_gitlab
from sync_pr_to_gitlab.git_ops import rebase_and_amend
from sync_pr_to_gitlab.git_ops import verify_commit_sha
from sync_pr_to_gitlab.github_client import check_forbidden_files
from sync_pr_to_gitlab.github_client import replace_sync_status_comment
from sync_pr_to_gitlab.github_client import validate_trigger_actor
from sync_pr_to_gitlab.gitlab_client import connect
from sync_pr_to_gitlab.gitlab_client import create_merge_request
from sync_pr_to_gitlab.gitlab_client import get_project

LABEL_MERGE = 'PR-Sync-Merge'
LABEL_REBASE = 'PR-Sync-Rebase'
LABEL_UPDATE = 'PR-Sync-Update'


def _check_update_label(pr_labels_list: list[dict]) -> None:
    label_validity = [label['name'] for label in pr_labels_list if label['name'] in (LABEL_MERGE, LABEL_REBASE)]
    if not label_validity:
        raise RuntimeError('PR-Sync-Update Label: Illegal use!')


def _sync_pr(
    pr_num: int,
    pr_head_branch: str,
    pr_commit_id: str,
    project: object,
    pr_base_branch: str,
    pr_html_url: str,
    rebase_flag: bool,
) -> None:
    try:
        project.branches.get(pr_head_branch)
    except GitlabGetError:
        pass
    else:
        raise RuntimeError('PR Merge/Rebase: Branch/MR already exists for PR!')

    fetch_pr(pr_num)
    checkout_pr_branch(pr_head_branch)
    verify_commit_sha(pr_commit_id)

    if rebase_flag:
        rebase_and_amend(pr_base_branch, pr_html_url)

    push_to_gitlab(pr_head_branch)


def _update_mr(pr_num: int, pr_head_branch: str, pr_commit_id: str, project: object) -> None:
    try:
        project.branches.get(pr_head_branch)
    except Exception as exc:
        raise RuntimeError('PR Update: No branch found on internal remote to update!') from exc

    fetch_pr(pr_num)
    checkout_pr_branch(pr_head_branch)
    verify_commit_sha(pr_commit_id)
    push_to_gitlab(pr_head_branch, force=True)


def main() -> None:
    if 'GITHUB_REPOSITORY' not in os.environ:
        print('Not running in GitHub action context, nothing to do')
        return

    github_workspace = os.environ.get('GITHUB_WORKSPACE')
    if github_workspace and os.path.exists(os.path.join(github_workspace, '.git')):
        os.chdir(github_workspace)

    cfg = Config.from_env()

    with open(os.environ['GITHUB_EVENT_PATH'], 'r', encoding='utf-8') as f:
        event = json.load(f)

    pr_label = event['label']['name']
    pr_labels_list = event['pull_request']['labels']

    pr_approve_labeller = event['sender']['login']
    pr_creator = event['pull_request']['user']['login']
    validate_trigger_actor(pr_creator, pr_approve_labeller)

    pr_comments_url = event['pull_request']['comments_url']
    pr_commit_id = str(event['pull_request']['head']['sha'])

    repo_fullname = event['repository']['full_name']

    pr_num = event['pull_request']['number']
    pr_head_branch = f'contrib/github_pr_{pr_num}'
    pr_rest_url = event['pull_request']['url']
    pr_html_url = event['pull_request']['html_url']
    pr_base_branch = event['pull_request']['base']['ref']

    pr_files_url = pr_rest_url + '/files'
    check_forbidden_files(pr_files_url, cfg.github_token)

    pr_title = event['pull_request']['title']
    pr_body = str(event['pull_request']['body'])

    gl = connect(cfg, repo_fullname, pr_base_branch)
    project = get_project(gl, cfg, repo_fullname)

    if pr_label == LABEL_REBASE:
        _sync_pr(pr_num, pr_head_branch, pr_commit_id, project, pr_base_branch, pr_html_url, rebase_flag=True)
    elif pr_label == LABEL_MERGE:
        _sync_pr(pr_num, pr_head_branch, pr_commit_id, project, pr_base_branch, pr_html_url, rebase_flag=False)
    elif pr_label == LABEL_UPDATE:
        _check_update_label(pr_labels_list)
        _update_mr(pr_num, pr_head_branch, pr_commit_id, project)
        replace_sync_status_comment(
            pr_comments_url,
            pr_label,
            pr_commit_id,
            pr_base_branch,
            pr_head_branch,
            pr_approve_labeller,
            cfg.github_token,
        )
        print('Done with the workflow!')
        return
    else:
        raise RuntimeError('Illegal program flow!')

    create_merge_request(project, pr_head_branch, pr_base_branch, pr_title, pr_body, pr_html_url)
    replace_sync_status_comment(
        pr_comments_url,
        pr_label,
        pr_commit_id,
        pr_base_branch,
        pr_head_branch,
        pr_approve_labeller,
        cfg.github_token,
    )
    print('Done with the workflow!')
