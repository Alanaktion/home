#!/usr/bin/python
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
    parser.add_argument("user", help="User or organization to clone")
    return parser


def get_user_repos(user: str) -> dict:
    conn = http.client.HTTPSConnection("api.github.com")
    headers = {"Accept": "application/json"}
    conn.request("GET", f"/users/{user}/repos", headers=headers)
    response = conn.getresponse()
    return json.loads(response.read())


def clone_repo(repo_info: dict, owner: str, gitargs: list[str] = []):
    name = repo_info["name"]

    # Skip existing cloned repositories
    if os.path.isdir(name):
        return

    url = f"https://github.com/{owner}/{name}.git"
    subprocess.run([GIT, "clone", url] + gitargs)


def main():
    args, gitargs = build_parser().parse_known_args()

    user_repos = get_user_repos(args.user)
    for repo in user_repos:
        clone_repo(repo, args.user, gitargs)


if __name__ == "__main__":
    main()
