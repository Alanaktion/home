#!/usr/bin/env bash
#
# dedupe-repos.sh — consolidate duplicate git clones into git worktrees.
#
# Scans a directory tree for git clones. Clones whose `origin` remote points at
# the same place are treated as duplicates of one another. For each such group,
# one clone is kept as the "primary"; every other clone is replaced in place by
# a worktree of the primary, checked out at the same commit.
#
set -euo pipefail

DRY_RUN=0
ASSUME_YES=0
ROOT="."

usage() {
  cat <<'EOF'
Usage: dedupe-repos.sh [-d DIR] [-n] [-y] [-h]

  -d DIR   directory to scan (default: current directory)
  -n       dry run: print the plan, change nothing
  -y       skip the confirmation prompt
  -h       show this help

How it works:
  1. Every clone under DIR (a directory containing a .git dir) is collected
     and grouped by its normalized origin URL.
  2. Groups with more than one clone are consolidated. The first clone in the
     group (sorted by path) becomes the primary.
  3. Each duplicate's local branches are imported into the primary. A branch
     name that already exists at a different commit gets suffixed with the
     duplicate's directory name.
  4. The duplicate is moved aside, a worktree is created at its original path,
     and the moved copy is deleted once the worktree is in place. If anything
     fails, the original is restored.

Clones with uncommitted changes are skipped.
EOF
}

say()  { printf '%s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }

# ---------------------------------------------------------------- arguments

while getopts ":d:nyh" opt; do
  case "$opt" in
    d) ROOT=$OPTARG ;;
    n) DRY_RUN=1 ;;
    y) ASSUME_YES=1 ;;
    h) usage; exit 0 ;;
    :) printf 'error: option -%s requires an argument\n' "$OPTARG" >&2; exit 2 ;;
    \?) printf 'error: unknown option -%s\n' "$OPTARG" >&2; exit 2 ;;
  esac
done
shift $((OPTIND - 1))

[ -d "$ROOT" ] || { printf 'error: not a directory: %s\n' "$ROOT" >&2; exit 1; }
ROOT=$(cd -- "$ROOT" && pwd)

# ------------------------------------------------------------- url handling

# Normalize a remote URL so that ssh/https/scp forms of the same repo collapse
# into one key:  git@github.com:me/x.git == https://github.com/me/x
normalize_url() {
  local u=$1
  u=${u%.git}
  u=${u%/}
  # scp-like syntax: [user@]host:path
  if [[ $u != *"://"* && $u == *:* ]]; then
    u=${u#*@}
    u=${u/:/\/}
  fi
  u=${u#*://}      # drop scheme
  u=${u##*@}       # drop userinfo
  u=${u%.git}
  u=${u%/}
  printf '%s\n' "${u,,}"
}

# ------------------------------------------------------------ collect clones

declare -A by_remote=()

while IFS= read -r gitdir; do
  repo=${gitdir%/.git}
  url=$(git -C "$repo" remote get-url origin 2>/dev/null) || continue
  [ -n "$url" ] || continue
  key=$(normalize_url "$url")
  by_remote[$key]="${by_remote[$key]:-}$repo"$'\n'
done < <(find "$ROOT" -type d -name .git -prune -print 2>/dev/null | sort)

# ------------------------------------------------------------------ build plan

mapfile -t remote_keys < <(printf '%s\n' "${!by_remote[@]}" | sort)

declare -a plan_primary=() plan_dup=()

for key in "${remote_keys[@]}"; do
  mapfile -t repos < <(printf '%s\n' "${by_remote[$key]}" | sed '/^$/d' | sort -u)
  ((${#repos[@]} > 1)) || continue
  primary=${repos[0]}
  for dup in "${repos[@]:1}"; do
    plan_primary+=("$primary")
    plan_dup+=("$dup")
  done
done

total=${#plan_dup[@]}
if ((total == 0)); then
  say "No duplicate clones found under $ROOT."
  exit 0
fi

say "Found $total duplicate clone(s) under $ROOT:"
i=0
while ((i < total)); do
  say ""
  say "  keep:  ${plan_primary[i]}"
  say "  fold:  ${plan_dup[i]}   ->  worktree"
  i=$((i + 1))
done
say ""

if ((DRY_RUN)); then
  say "Dry run: nothing changed."
  exit 0
fi

if ((!ASSUME_YES)); then
  printf 'Proceed? [y/N] '
  read -r reply || reply=""
  case "$reply" in
    [yY]*) ;;
    *) say "Aborted."; exit 1 ;;
  esac
fi

# ------------------------------------------------------------------- folding

fold_duplicate() {
  local primary=$1 dup=$2

  if [ -n "$(git -C "$dup" status --porcelain 2>/dev/null)" ]; then
    warn "skipping $dup: working tree has uncommitted changes"
    return 1
  fi

  local head
  if ! head=$(git -C "$dup" rev-parse --verify HEAD 2>/dev/null); then
    warn "skipping $dup: repository has no commits"
    return 1
  fi

  # Import every object and branch out of the duplicate into the primary.
  if ! git -C "$primary" fetch --quiet --no-tags "$dup" \
        '+refs/heads/*:refs/dedupe-tmp/*' \
        '+HEAD:refs/dedupe-tmp/HEAD' 2>/dev/null; then
    warn "skipping $dup: could not import objects into $primary"
    return 1
  fi

  # Recreate the duplicate's branches inside the primary, renaming on conflict.
  local -A name_map=()
  local ref b sha target n
  while IFS= read -r ref; do
    if [ -n "$ref" ]; then
      b=${ref#refs/dedupe-tmp/}
      if [ "$b" != "HEAD" ]; then
        sha=$(git -C "$primary" rev-parse --verify "refs/dedupe-tmp/$b")
        target=$b
        if git -C "$primary" show-ref --verify --quiet "refs/heads/$target"; then
          if [ "$(git -C "$primary" rev-parse "refs/heads/$target")" = "$sha" ]; then
            name_map[$b]=$target
            continue
          fi
          target="$b-$(basename -- "$dup")"
          n=2
          while git -C "$primary" show-ref --verify --quiet "refs/heads/$target"; do
            target="$b-$(basename -- "$dup")-$n"
            n=$((n + 1))
          done
        fi
        git -C "$primary" branch "$target" "$sha"
        name_map[$b]=$target
      fi
    fi
  done < <(git -C "$primary" for-each-ref --format='%(refname)' refs/dedupe-tmp/)

  # Which branch should the new worktree land on?
  local branch target primary_branch use_detach=0
  branch=$(git -C "$dup" symbolic-ref --quiet --short HEAD || true)

  if [ -n "$branch" ] && [ -n "${name_map[$branch]:-}" ]; then
    target=${name_map[$branch]}
    primary_branch=$(git -C "$primary" symbolic-ref --quiet --short HEAD || true)
    # A branch can only be checked out in one worktree at a time.
    [ "$target" = "$primary_branch" ] && use_detach=1
  else
    use_detach=1
  fi

  # Drop the temporary import refs; the branches we just made keep the objects.
  while IFS= read -r ref; do
    if [ -n "$ref" ]; then
      git -C "$primary" update-ref -d "$ref"
    fi
  done < <(git -C "$primary" for-each-ref --format='%(refname)' refs/dedupe-tmp/)

  # Swap the duplicate for a worktree at the same path.
  local backup="${dup}.dedupe-backup.$$"
  mv -- "$dup" "$backup"

  local ok=1
  if [ "$use_detach" = 1 ]; then
    git -C "$primary" worktree add --detach "$dup" "$head" || ok=0
  else
    git -C "$primary" worktree add "$dup" "$target" || ok=0
  fi

  if [ "$ok" = 1 ]; then
    rm -rf -- "$backup"
    if [ "$use_detach" = 1 ]; then
      say "  folded $dup  (detached at ${head:0:8})"
    else
      say "  folded $dup  (branch $target)"
    fi
  else
    mv -- "$backup" "$dup"
    git -C "$primary" worktree prune
    warn "failed to create worktree at $dup; original restored"
    return 1
  fi
}

# --------------------------------------------------------------------- run

failures=0
i=0
while ((i < total)); do
  ( fold_duplicate "${plan_primary[i]}" "${plan_dup[i]}" ) || failures=$((failures + 1))
  i=$((i + 1))
done

say ""
if ((failures == 0)); then
  say "Done. Folded $total clone(s) into worktrees."
else
  say "Done with $failures failure(s)."
fi
