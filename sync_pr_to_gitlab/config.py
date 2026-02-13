from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    github_token: str
    gitlab_url: str
    gitlab_token: str
    gitlab_namespace: str
    git_config_name: str
    git_config_email: str

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            github_token=os.environ['GITHUB_TOKEN'],
            gitlab_url=os.environ['GITLAB_URL'],
            gitlab_token=os.environ['GITLAB_TOKEN'],
            gitlab_namespace=os.environ.get('GITLAB_NAMESPACE', ''),
            git_config_name=os.environ.get('GIT_CONFIG_NAME', ''),
            git_config_email=os.environ.get('GIT_CONFIG_EMAIL', ''),
        )
