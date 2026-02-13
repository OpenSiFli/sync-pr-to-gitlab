from __future__ import annotations

import re

import requests


def check_approver(pr_creator: str, pr_comments_url: str, pr_approve_labeller: str, github_token: str) -> str:
    print('Checking PR comment and affixed label...')
    res = requests.get(pr_comments_url, headers={'Authorization': 'token ' + github_token}, timeout=30)
    r_data = res.json()

    for comment in reversed(r_data):
        comment_body = comment['body']
        if bool(re.match('sha=', comment_body, re.I)) and comment['user']['login'] == pr_approve_labeller != pr_creator:
            return comment_body[4:]

    raise RuntimeError('PR Comment Error: Ensure that Command comment exists and PR commenter and labeller match!')


def check_forbidden_files(pr_files_url: str, github_token: str) -> None:
    print('Checking if PR modified forbidden files...')
    res = requests.get(pr_files_url, headers={'Authorization': 'token ' + github_token}, timeout=30)
    r_data = res.json()

    pr_files = [
        file_info['filename']
        for file_info in r_data
        if '.gitlab' in file_info['filename'] or '.github' in file_info['filename']
    ]
    if pr_files:
        raise RuntimeError('PR modifying forbidden files!!!')
