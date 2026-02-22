from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any

import requests

SYNC_STATUS_MARKER = '<!-- sync-pr-to-gitlab:sync-status -->'


def _auth_headers(github_token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {github_token}'}


def validate_trigger_actor(pr_creator: str, pr_approve_labeller: str) -> None:
    print('Validating label trigger actor...')
    if pr_creator == pr_approve_labeller:
        raise RuntimeError('PR Trigger Error: PR creator cannot apply sync labels!')


def list_comments(pr_comments_url: str, github_token: str) -> list[dict[str, Any]]:
    print('Fetching PR comments...')
    res = requests.get(pr_comments_url, headers=_auth_headers(github_token), timeout=30)
    res.raise_for_status()
    comments = res.json()
    if not isinstance(comments, list):
        raise RuntimeError('GitHub API Error: Expected a list response for PR comments!')
    return comments


def delete_comment(comment_url: str, github_token: str) -> None:
    print('Deleting old sync status comment...')
    res = requests.delete(comment_url, headers=_auth_headers(github_token), timeout=30)
    res.raise_for_status()


def create_comment(pr_comments_url: str, comment_body: str, github_token: str) -> None:
    print('Creating sync status comment...')
    res = requests.post(pr_comments_url, headers=_auth_headers(github_token), json={'body': comment_body}, timeout=30)
    res.raise_for_status()


def _build_sync_status_comment(
    mode: str,
    github_pr_sha: str,
    target_branch: str,
    source_branch: str,
    triggered_by: str,
) -> str:
    synced_at = datetime.now(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    return (
        f'{SYNC_STATUS_MARKER}\n'
        '✅ Sync to GitLab succeeded\n\n'
        f'- Mode: {mode}\n'
        f'- GitHub PR SHA: {github_pr_sha}\n'
        f'- Target Branch: {target_branch}\n'
        f'- GitLab Source Branch: {source_branch}\n'
        f'- Triggered By: @{triggered_by}\n'
        f'- Synced At (UTC): {synced_at}'
    )


def replace_sync_status_comment(  # pylint: disable=too-many-arguments
    pr_comments_url: str,
    mode: str,
    github_pr_sha: str,
    target_branch: str,
    source_branch: str,
    triggered_by: str,
    github_token: str,
) -> None:
    comments = list_comments(pr_comments_url, github_token)

    managed_comments = [comment for comment in comments if SYNC_STATUS_MARKER in str(comment.get('body', ''))]
    for comment in managed_comments:
        comment_url = str(comment.get('url', ''))
        if not comment_url:
            raise RuntimeError('GitHub Comment Error: Sync status comment has no URL.')
        delete_comment(comment_url, github_token)

    comment_body = _build_sync_status_comment(mode, github_pr_sha, target_branch, source_branch, triggered_by)
    create_comment(pr_comments_url, comment_body, github_token)


def check_forbidden_files(pr_files_url: str, github_token: str) -> None:
    print('Checking if PR modified forbidden files...')
    res = requests.get(pr_files_url, headers=_auth_headers(github_token), timeout=30)
    res.raise_for_status()
    r_data = res.json()

    pr_files = [
        file_info['filename']
        for file_info in r_data
        if '.gitlab' in file_info['filename'] or '.github' in file_info['filename']
    ]
    if pr_files:
        raise RuntimeError('PR modifying forbidden files!!!')
