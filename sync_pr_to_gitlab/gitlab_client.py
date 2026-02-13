from __future__ import annotations

import gitlab
from git import Git

from sync_pr_to_gitlab.config import Config

GITLAB_REMOTE = 'gitlab'


def connect(cfg: Config, repo_fullname: str, pr_base_branch: str) -> gitlab.Gitlab:
    print('Connecting to GitLab...')
    gl = gitlab.Gitlab(url=f'https://{cfg.gitlab_url}', private_token=cfg.gitlab_token)
    gl.auth()

    project_name = repo_fullname.split('/')[-1]
    namespace = cfg.gitlab_namespace or repo_fullname.split('/')[0]
    gl_project_url = f'https://private-token:{cfg.gitlab_token}@{cfg.gitlab_url}/{namespace}/{project_name}.git'

    git = Git('.')
    print('Adding and fetching the internal remote...')
    git.remote('add', GITLAB_REMOTE, gl_project_url)
    git.pull(GITLAB_REMOTE, pr_base_branch)

    return gl


def get_project(gl: gitlab.Gitlab, cfg: Config, repo_fullname: str) -> gitlab.v4.objects.Project:
    namespace = cfg.gitlab_namespace or repo_fullname.split('/')[0]
    project_name = repo_fullname.split('/')[-1]
    return gl.projects.get(f'{namespace}/{project_name}')


def create_merge_request(
    project: gitlab.v4.objects.Project,
    pr_head_branch: str,
    pr_base_branch: str,
    pr_title: str,
    pr_body: str,
    pr_html_url: str,
) -> None:
    print('Creating a merge request...')
    mr = project.mergerequests.create(
        {
            'source_branch': pr_head_branch,
            'target_branch': pr_base_branch,
            'title': pr_title + ' (GitHub PR)',
            'remove_source_branch': True,
        }
    )

    print('Updating merge request description...')
    mr_desc = f'## Description\n{pr_body}\n\n## Related\n* Merges {pr_html_url}'
    mr.description = mr_desc
    mr.save()
