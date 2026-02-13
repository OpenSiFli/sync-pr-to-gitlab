from __future__ import annotations

import os

from git import Git
from git import Repo
from gitlab.exceptions import GitlabGetError

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
    print('Checking whether specified commit ID matches with user branch HEAD...')
    git = Git('.')
    expected = git.rev_parse('--short', 'HEAD')
    if not pr_commit_id.startswith(expected):
        raise RuntimeError('PR Commit SHA1 in workflow comment and user branch do not match!')


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
    git.rebase(pr_base_branch)

    commit = repo.head.commit
    new_msg = f'{commit.message}\n\nCloses {pr_html_url}'
    print('Amending commit message...')
    git.execute(['git', 'commit', '--amend', '-m', new_msg])
