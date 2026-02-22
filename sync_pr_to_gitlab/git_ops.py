from __future__ import annotations

import os

from git import Git
from git import Repo

GITHUB_REMOTE = 'origin'
GITLAB_REMOTE = 'gitlab'


def fetch_pr(pr_num: int) -> None:
    print('Fetching the PR branch...')
    git = Git('.')
    git.fetch(GITHUB_REMOTE, f'pull/{pr_num}/head')


def checkout_pr_branch(pr_head_branch: str) -> None:
    print('Checking out the PR branch...')
    git = Git('.')
    git.checkout('FETCH_HEAD', b=pr_head_branch)


def verify_commit_sha(pr_commit_id: str) -> None:
    print('Checking whether event commit ID matches current PR HEAD...')
    git = Git('.')
    expected_commit = git.rev_parse('HEAD')
    if not (pr_commit_id.startswith(expected_commit) or expected_commit.startswith(pr_commit_id)):
        raise RuntimeError('PR commit SHA from label event does not match current PR HEAD. Re-apply label after latest push.')


def push_to_gitlab(pr_head_branch: str, force: bool = False) -> None:
    print('Pushing to remote...')
    git = Git('.')
    if force:
        git.push('--force', GITLAB_REMOTE, pr_head_branch)
    else:
        git.push('--set-upstream', GITLAB_REMOTE, pr_head_branch)


def rebase_and_amend(pr_base_branch: str, pr_html_url: str) -> None:
    repo = Repo('.')
    repo.config_writer().set_value('user', 'name', os.environ['GIT_CONFIG_NAME']).release()
    repo.config_writer().set_value('user', 'email', os.environ['GIT_CONFIG_EMAIL']).release()

    git = Git('.')
    print(f'Rebasing with the latest {pr_base_branch} branch...')
    git.rebase(f'{GITLAB_REMOTE}/{pr_base_branch}')

    commit = repo.head.commit
    new_msg = f'{commit.message}\n\nCloses {pr_html_url}'
    print('Amending commit message...')
    git.execute(['git', 'commit', '--amend', '-m', new_msg])
