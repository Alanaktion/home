#!/usr/bin/env python3
import argparse
import http.client
import json
import os
import shutil
import subprocess


GIT = shutil.which("git") or "git"


def build_parser():
    parser = argparse.ArgumentParser(
        description="clone all GitHub repositories for a user/org",
        epilog="additional arguments will be passed to `git clone`")
    parser.add_argument("user", help="user or organization to clone")
    parser.add_argument("--ssh", action="store_true",
                        help="clone using SSH instead of HTTPS")
    return parser


def get_user_repos(user: str) -> dict:
    conn = http.client.HTTPSConnection("api.github.com")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "alanaktion",
    }
    conn.request("GET", f"/users/{user}/repos", headers=headers)
    response = conn.getresponse()
    return json.loads(response.read())


def clone_repo(repo_info: dict, owner: str, ssh: bool = False, gitargs: list[str] = []):
    name = repo_info["name"]

    # Skip existing cloned repositories
    if os.path.isdir(name):
        return

    if ssh:
        url = f"git@github.com:{owner}/{name}.git"
    else:
        url = f"https://github.com/{owner}/{name}.git"
    subprocess.run([GIT, "clone", url] + gitargs)


def main():
    args, gitargs = build_parser().parse_known_args()

    user_repos = get_user_repos(args.user)
    for repo in user_repos:
        clone_repo(repo, args.user, args.ssh, gitargs)


if __name__ == "__main__":
    main()
