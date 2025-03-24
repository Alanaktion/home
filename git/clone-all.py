#!/usr/bin/env python3
import argparse
import fnmatch
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
    parser.add_argument("--filter", help="only clone repos matching pattern")
    parser.add_argument("--ssh", action="store_true",
                        help="clone using SSH instead of HTTPS")
    return parser


def get_user_repos(user: str) -> list:
    conn = http.client.HTTPSConnection("api.github.com")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "alanaktion",
    }

    repos = []

    # Initial request to fetch the first page of repositories
    conn.request("GET", f"/users/{user}/repos", headers=headers)
    response = conn.getresponse()
    data = response.read()

    with open('headers.raw', 'a') as f:
        print(response.getheaders(), file=f)

    if not data:
        return []

    repos.extend(json.loads(data))

    # Check for pagination links
    link_header = response.getheader("Link")
    while link_header:
        links = parse_link_header(link_header)
        if 'next' in links:
            conn.request("GET", links['next'], headers=headers)
            response = conn.getresponse()
            data = response.read()
            repos.extend(json.loads(data))
            link_header = response.getheader("Link")
        else:
            break

    return repos


def parse_link_header(link_header) -> dict[str,str]:
    # <https://api.github.com/user/236490/repos?page=2>; rel="next", <https://api.github.com/user/236490/repos?page=6>; rel="last"
    links = {}

    for part in link_header.split(", "):
        try:
            # Split each part into URL and rel attributes
            url_raw, rel_raw = part.split("; rel=\"")
            url = url_raw.strip("<>")
            rel = rel_raw.strip("\"")

            if rel not in links:
                links[rel] = url
        except:
            pass
    return links


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
        if args.filter and not fnmatch.fnmatch(repo["name"], args.filter):
            continue
        clone_repo(repo, args.user, args.ssh, gitargs)


if __name__ == "__main__":
    main()
